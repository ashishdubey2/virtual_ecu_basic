#pragma once

#include "engine_controller.h"

#include <linux/can.h>
#include <string>

class CanHandler {
public:
    explicit CanHandler(const std::string& interface_name);
    ~CanHandler();

    CanHandler(const CanHandler&) = delete;
    CanHandler& operator=(const CanHandler&) = delete;

    bool receive(EngineInput& input);
    void send(const EngineOutput& output);

private:
    int socket_fd_;
};
