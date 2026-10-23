#include "../../share/json_helper.hpp"
#include "../../share/manipulator_helper.hpp"
#include "manipulator/manipulators/post_event_to_virtual_devices/post_event_to_virtual_devices.hpp"
#include "run_loop_thread_utility.hpp"
#include <boost/ut.hpp>

int main(void) {
  using namespace boost::ut;
  using namespace boost::ut::literals;

  auto scoped_dispatcher_manager = krbn::dispatcher_utility::initialize_dispatchers();
  auto scoped_run_loop_thread_manager = krbn::run_loop_thread_utility::initialize_shared_run_loop_thread();

  "sleep shortcut reports"_test = [] {
    using namespace krbn;
    using namespace std::chrono_literals;
    const auto run = [](const std::string& bundle_identifier,
                        const nlohmann::json& key,
                        const nlohmann::json& original_key,
                        bool with_sleep_modifiers,
                        std::chrono::milliseconds delay, int release_time = 160, bool leave_loginwindow = false, bool disconnect = false) {
      manipulator::manipulators::post_event_to_virtual_devices::post_event_to_virtual_devices m({}, {});
      m.set_sleep_shortcut_delay(delay);
      event_queue::queue input;
      auto output = std::make_shared<event_queue::queue>();
      pqrs::osx::frontmost_application_monitor::application application;
      if (!bundle_identifier.empty()) {
        application.set_bundle_identifier(bundle_identifier);
      }
      output->get_manipulator_environment().set_frontmost_application(application);
      const auto send = [&](const nlohmann::json& value,
                            const nlohmann::json& original,
                            event_type type,
                            int milliseconds) {
        const auto time = absolute_time_point(0) +
                          pqrs::osx::chrono::make_absolute_time_duration(std::chrono::milliseconds(milliseconds));
        const event_queue::event event(value.get<momentary_switch_event>());
        event_queue::entry entry(device_id(1), event_queue::event_time_stamp(time),
                                 event, type, std::nullopt,
                                 event_queue::event(original.get<momentary_switch_event>()),
                                 event_queue::state::original);
        m.manipulate(entry, input, output, time);
      };
      if (with_sleep_modifiers) {
        // Cover the right-hand variants too.
        send({{"key_code", "right_command"}}, {{"key_code", "right_command"}}, event_type::key_down, 10);
        send({{"key_code", "right_option"}}, {{"key_code", "right_option"}}, event_type::key_down, 20);
      }
      send(key, original_key, event_type::key_down, 100);
      if (bundle_identifier == "com.apple.loginwindow" && key == nlohmann::json{{"key_code", "escape"}}) {
        expect(m.get_queue().get_events().empty());
      }
      if (leave_loginwindow) {
        application.set_bundle_identifier("com.apple.Terminal");
        output->get_manipulator_environment().set_frontmost_application(application);
      }
      if (disconnect) {
        m.handle_device_ungrabbed_event(device_id(1), *output, absolute_time_point(0));
      }
      send(key, original_key, event_type::key_up, release_time);
      return nlohmann::json(m.get_queue().get_events());
    };

    const nlohmann::json escape{{"key_code", "escape"}};
    for (const auto& original : {escape, nlohmann::json{{"key_code", "caps_lock"}}}) {
      const auto reports = run("com.apple.loginwindow", escape, original, false, 500ms);
      expect(reports.size() == 2_ul);
      expect(reports.at(0).at("time_stamp") == 160);
      expect(reports.at(1).at("time_stamp") == 165);
      expect(reports.at(0).at("keyboard_input").at("keys") == nlohmann::json::array({escape}));
      expect(reports.at(1).at("keyboard_input").at("keys").empty());
    }

    {
      const auto reports = run("com.apple.loginwindow", escape, escape, false, 500ms, 2100);
      expect(reports.size() == 2_ul);
      expect(reports.at(0).at("time_stamp").get<int>() >= 2099);
      expect(reports.at(0).at("time_stamp").get<int>() <= 2100);
      expect(reports.at(1).at("time_stamp").get<int>() >= 2104);
      expect(reports.at(1).at("time_stamp").get<int>() <= 2105);
    }

    expect(run("com.apple.loginwindow", escape, escape, false, 500ms, 160, true).empty());
    expect(run("com.apple.loginwindow", escape, escape, false, 500ms, 160, false, true).empty());

    for (const auto& bundle : {"com.apple.Terminal", ""}) {
      const auto reports = run(bundle, escape, escape, false, 500ms);
      expect(reports.at(0).at("time_stamp") == 100);
      expect(reports.at(1).at("time_stamp") == 160);
    }
    {
      const nlohmann::json key{{"key_code", "a"}};
      const auto reports = run("com.apple.loginwindow", key, key, false, 500ms);
      expect(reports.at(0).at("time_stamp") == 100);
      expect(reports.at(1).at("time_stamp") == 160);
    }
    {
      const auto reports = run("com.apple.loginwindow", escape, escape, false, 0ms);
      expect(reports.at(0).at("time_stamp") == 160);
      expect(reports.at(1).at("time_stamp") == 165);
      const auto custom = run("com.apple.loginwindow", escape, escape, false, 750ms);
      expect(custom.at(0).at("time_stamp") == 160);
      expect(custom.at(1).at("time_stamp") == 165);
    }
    for (const auto& key : {nlohmann::json{{"key_code", "power"}},
                            nlohmann::json{{"consumer_key_code", "power"}},
                            nlohmann::json{{"consumer_key_code", "eject"}}}) {
      const auto reports = run("com.apple.Terminal", key, key, true, 500ms);
      expect(reports.at(reports.size() - 2).at("time_stamp") == 600);
      expect(reports.back().at("time_stamp") == 605);
      const auto plain = run("com.apple.Terminal", key, key, false, 500ms);
      expect(plain.at(0).at("time_stamp") == 100);
      expect(plain.at(1).at("time_stamp") == 160);
    }
  };

  "actual examples"_test = [] {
    auto helper = std::make_unique<krbn::unit_testing::manipulator_helper>();

    helper->run_tests(krbn::unit_testing::json_helper::load_jsonc("json/tests.json"));

    helper = nullptr;
  };

  "mouse_key_handler.count_converter"_test = [] {
    {
      krbn::manipulator::manipulators::post_event_to_virtual_devices::mouse_key_handler::count_converter count_converter(64);
      expect(count_converter.update(32) == static_cast<uint8_t>(0));
      expect(count_converter.update(32) == static_cast<uint8_t>(1));
      expect(count_converter.update(32) == static_cast<uint8_t>(0));
      expect(count_converter.update(32) == static_cast<uint8_t>(1));

      expect(count_converter.update(16) == static_cast<uint8_t>(0));
      expect(count_converter.update(16) == static_cast<uint8_t>(0));
      expect(count_converter.update(16) == static_cast<uint8_t>(0));
      expect(count_converter.update(16) == static_cast<uint8_t>(1));

      expect(count_converter.update(-16) == static_cast<uint8_t>(0));
      expect(count_converter.update(-16) == static_cast<uint8_t>(0));
      expect(count_converter.update(-16) == static_cast<uint8_t>(0));
      expect(count_converter.update(-16) == static_cast<uint8_t>(-1));
    }
    {
      krbn::manipulator::manipulators::post_event_to_virtual_devices::mouse_key_handler::count_converter count_converter(64);
      expect(count_converter.update(128) == static_cast<uint8_t>(2));
      expect(count_converter.update(128) == static_cast<uint8_t>(2));
      expect(count_converter.update(-128) == static_cast<uint8_t>(-2));
      expect(count_converter.update(-128) == static_cast<uint8_t>(-2));
    }
  };

  return 0;
}
