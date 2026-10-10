#include "can_handler.h"
#include "engine_controller.h"

#include <csignal>
#include <exception>
#include <iostream>
#include <string>

namespace {
volatile std::sig_atomic_t keep_running = 1;

void handle_signal(int)
{
    keep_running = 0;
}
}

int main(int argc, char* argv[])
{
    if (argc > 2) {
        std::cerr << "Usage: " << argv[0] << " [can-interface]\n";
        return 2;
    }

    const std::string interface_name = argc == 2 ? argv[1] : "vcan0";
    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    try {
        CanHandler can(interface_name);
        EngineController controller;
        std::cout << "Virtual engine ECU listening on " << interface_name
                  << " (CAN 0x100 -> 0x200). Press Ctrl+C to stop.\n";

        while (keep_running) {
            EngineInput input{};
            if (can.receive(input)) {
                can.send(controller.update(input));
            }
        }
    } catch (const std::exception& error) {
        std::cerr << "Virtual ECU error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
