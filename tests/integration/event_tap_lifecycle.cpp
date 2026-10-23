#include "dispatcher_utility.hpp"
#include "monitor/event_tap_monitor.hpp"
#include <algorithm>
#include <array>
#include <iostream>
#include <unistd.h>

class barrier final : pqrs::dispatcher::extra::dispatcher_client {
public:
  ~barrier() { detach_from_dispatcher(); }
  void sync() {
    auto wait = pqrs::make_thread_wait();
    enqueue_to_dispatcher([wait] { wait->notify(); });
    wait->wait_notice();
  }
};

int count_taps() {
  std::array<CGEventTapInformation, 1024> taps{};
  uint32_t count = 0;
  if (CGGetEventTapList(taps.size(), taps.data(), &count) != kCGErrorSuccess) return -1;
  return std::count_if(taps.begin(), taps.begin() + std::min<size_t>(count, taps.size()),
                       [](auto& tap) { return tap.tappingProcess == getpid(); });
}

int main() {
  auto dispatcher = krbn::dispatcher_utility::initialize_dispatchers();
  barrier b;
  const auto before = count_taps();
  if (before < 0) {
    std::cerr << "Unable to enumerate event taps\n";
    return 1;
  }
  for (int i = 0; i < 10; ++i) {
    auto monitor = std::make_unique<krbn::event_tap_monitor>();
    monitor->async_start();
    b.sync();
    if (i == 0 && count_taps() <= before) {
      std::cerr << "SKIP: event tap creation is not permitted for this test process\n";
      return 77;
    }
    monitor.reset();
  }
  const auto after = count_taps();
  std::cout << "Own taps before=" << before << " after=" << after << "\n";
  return after == before ? 0 : 1;
}
