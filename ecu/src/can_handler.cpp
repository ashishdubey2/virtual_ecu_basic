#include "can_handler.h"

#include <cerrno>
#include <cstring>
#include <iostream>
#include <linux/can/raw.h>
#include <net/if.h>
#include <poll.h>
#include <stdexcept>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

namespace {
constexpr canid_t kInputCanId = 0x100;
constexpr canid_t kOutputCanId = 0x200;
constexpr std::size_t kPayloadSize = 4;
}

CanHandler::CanHandler(const std::string& interface_name)
    : socket_fd_(socket(PF_CAN, SOCK_RAW, CAN_RAW))
{
    if (socket_fd_ < 0) {
        throw std::runtime_error("Unable to open SocketCAN socket: " +
                                 std::string(std::strerror(errno)));
    }

    try {
        const unsigned int interface_index = if_nametoindex(interface_name.c_str());
        if (interface_index == 0) {
            throw std::runtime_error("Unknown CAN interface '" + interface_name +
                                     "': " + std::string(std::strerror(errno)));
        }

        const can_filter filter{kInputCanId,
                                CAN_EFF_FLAG | CAN_RTR_FLAG | CAN_SFF_MASK};
        if (setsockopt(socket_fd_, SOL_CAN_RAW, CAN_RAW_FILTER, &filter,
                       sizeof(filter)) < 0) {
            throw std::runtime_error("Unable to set CAN receive filter: " +
                                     std::string(std::strerror(errno)));
        }

        sockaddr_can address{};
        address.can_family = AF_CAN;
        address.can_ifindex = static_cast<int>(interface_index);
        if (bind(socket_fd_, reinterpret_cast<sockaddr*>(&address),
                 sizeof(address)) < 0) {
            throw std::runtime_error("Unable to bind CAN interface '" +
                                     interface_name + "': " +
                                     std::string(std::strerror(errno)));
        }
    } catch (...) {
        close(socket_fd_);
        socket_fd_ = -1;
        throw;
    }
}

CanHandler::~CanHandler()
{
    if (socket_fd_ >= 0) {
        close(socket_fd_);
    }
}

bool CanHandler::receive(EngineInput& input)
{
    pollfd descriptor{socket_fd_, POLLIN, 0};
    const int ready = poll(&descriptor, 1, 100);
    if (ready < 0) {
        if (errno == EINTR) {
            return false;
        }
        throw std::runtime_error("CAN receive poll failed: " +
                                 std::string(std::strerror(errno)));
    }
    if (ready == 0) {
        return false;
    }
    if ((descriptor.revents & (POLLERR | POLLHUP | POLLNVAL)) != 0) {
        throw std::runtime_error("CAN interface reported a socket error");
    }
    if ((descriptor.revents & POLLIN) == 0) {
        return false;
    }

    can_frame frame{};
    const ssize_t bytes_read = read(socket_fd_, &frame, sizeof(frame));
    if (bytes_read < 0) {
        if (errno == EINTR) {
            return false;
        }
        throw std::runtime_error("CAN receive failed: " +
                                 std::string(std::strerror(errno)));
    }
    if (bytes_read != static_cast<ssize_t>(CAN_MTU)) {
        throw std::runtime_error("Received a CAN frame with an unexpected size");
    }
    if (frame.can_dlc != kPayloadSize) {
        std::cerr << "Ignoring CAN 0x100 frame with " << frame.can_dlc
                  << " data bytes; expected 4.\n";
        return false;
    }

    input.rpm = static_cast<std::uint16_t>(
        (static_cast<std::uint16_t>(frame.data[0]) << 8) | frame.data[1]);
    input.throttle_percent = frame.data[2];
    const int raw_temperature = frame.data[3];
    input.coolant_temperature_c = static_cast<std::int8_t>(
        raw_temperature <= 127 ? raw_temperature : raw_temperature - 256);
    return true;
}

void CanHandler::send(const EngineOutput& output)
{
    can_frame frame{};
    frame.can_id = kOutputCanId;
    frame.can_dlc = kPayloadSize;
    frame.data[0] = static_cast<std::uint8_t>(output.calculated_rpm >> 8);
    frame.data[1] = static_cast<std::uint8_t>(output.calculated_rpm & 0xFF);
    frame.data[2] = static_cast<std::uint8_t>(output.state);
    frame.data[3] = output.fault_status;

    const ssize_t bytes_written = write(socket_fd_, &frame, CAN_MTU);
    if (bytes_written < 0) {
        throw std::runtime_error("CAN transmit failed: " +
                                 std::string(std::strerror(errno)));
    }
    if (bytes_written != CAN_MTU) {
        throw std::runtime_error("CAN transmit wrote an incomplete frame");
    }
}
