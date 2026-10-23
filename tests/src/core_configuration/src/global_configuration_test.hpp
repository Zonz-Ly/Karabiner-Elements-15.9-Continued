#include "core_configuration/core_configuration.hpp"
#include <boost/ut.hpp>

void run_global_configuration_test(void) {
  using namespace boost::ut;
  using namespace boost::ut::literals;

  "sleep shortcut delay configuration"_test = [] {
    using configuration = krbn::core_configuration::details::global_configuration;
    const auto handling = krbn::core_configuration::error_handling::strict;
    configuration defaults(nlohmann::json::object(), handling);
    expect(defaults.get_delay_milliseconds_before_sleep_shortcut() == 500_i);
    expect(!defaults.to_json().contains("delay_milliseconds_before_sleep_shortcut"));
    for (const auto& [input, expected] : std::vector<std::pair<int, int>>{{-1, 0}, {0, 0}, {750, 750}, {20000, 10000}}) {
      configuration c({{"delay_milliseconds_before_sleep_shortcut", input}}, handling);
      expect(c.get_delay_milliseconds_before_sleep_shortcut() == expected);
      expect(c.to_json().at("delay_milliseconds_before_sleep_shortcut") == expected);
      defaults.set_delay_milliseconds_before_sleep_shortcut(input);
      expect(defaults.get_delay_milliseconds_before_sleep_shortcut() == expected);
    }
  };

  "global_configuration"_test = [] {
    // empty json
    {
      auto json = nlohmann::json::object();
      krbn::core_configuration::details::global_configuration global_configuration(json,
                                                                                   krbn::core_configuration::error_handling::strict);
      expect(global_configuration.get_show_in_menu_bar() == true);
      expect(global_configuration.get_show_profile_name_in_menu_bar() == false);
      expect(global_configuration.get_show_additional_menu_items() == false);
      expect(global_configuration.get_enable_notification_window() == true);
      expect(global_configuration.get_ask_for_confirmation_before_quitting() == true);
      expect(global_configuration.get_unsafe_ui() == false);
      expect(global_configuration.get_filter_useless_events_from_specific_devices() == true);
      expect(global_configuration.get_reorder_same_timestamp_input_events_to_prioritize_modifiers() == true);
    }

    // load values from json
    {
      nlohmann::json json{
          {"show_in_menu_bar", false},
          {"show_profile_name_in_menu_bar", true},
          {"show_additional_menu_items", true},
          {"enable_notification_window", false},
          {"ask_for_confirmation_before_quitting", false},
          {"unsafe_ui", true},
          {"filter_useless_events_from_specific_devices", false},
          {"reorder_same_timestamp_input_events_to_prioritize_modifiers", false},
      };
      krbn::core_configuration::details::global_configuration global_configuration(json,
                                                                                   krbn::core_configuration::error_handling::strict);
      expect(global_configuration.get_show_in_menu_bar() == false);
      expect(global_configuration.get_show_profile_name_in_menu_bar() == true);
      expect(global_configuration.get_show_additional_menu_items() == true);
      expect(global_configuration.get_enable_notification_window() == false);
      expect(global_configuration.get_ask_for_confirmation_before_quitting() == false);
      expect(global_configuration.get_unsafe_ui() == true);
      expect(global_configuration.get_filter_useless_events_from_specific_devices() == false);
      expect(global_configuration.get_reorder_same_timestamp_input_events_to_prioritize_modifiers() == false);

      //
      // Set default values
      //

      global_configuration.set_show_in_menu_bar(true);
      global_configuration.set_show_profile_name_in_menu_bar(false);
      global_configuration.set_show_additional_menu_items(false);
      global_configuration.set_enable_notification_window(true);
      global_configuration.set_ask_for_confirmation_before_quitting(true);
      global_configuration.set_unsafe_ui(false);
      global_configuration.set_filter_useless_events_from_specific_devices(true);
      global_configuration.set_reorder_same_timestamp_input_events_to_prioritize_modifiers(true);
      nlohmann::json j(global_configuration);
      expect(j.empty());
    }

    // invalid values in json
    {
      nlohmann::json json{
          {"show_in_menu_bar", 0},
          {"show_profile_name_in_menu_bar", nlohmann::json::object()},
          {"show_additional_menu_items", nlohmann::json::object()},
          {"enable_notification_window", nlohmann::json::object()},
          {"unsafe_ui", nlohmann::json::object()},
          {"filter_useless_events_from_specific_devices", nlohmann::json::object()},
          {"reorder_same_timestamp_input_events_to_prioritize_modifiers", nlohmann::json::object()},
      };
      krbn::core_configuration::details::global_configuration global_configuration(json,
                                                                                   krbn::core_configuration::error_handling::loose);
      expect(global_configuration.get_show_in_menu_bar() == true);
      expect(global_configuration.get_show_profile_name_in_menu_bar() == false);
      expect(global_configuration.get_show_additional_menu_items() == false);
      expect(global_configuration.get_enable_notification_window() == true);
      expect(global_configuration.get_ask_for_confirmation_before_quitting() == true);
      expect(global_configuration.get_unsafe_ui() == false);
      expect(global_configuration.get_filter_useless_events_from_specific_devices() == true);
      expect(global_configuration.get_reorder_same_timestamp_input_events_to_prioritize_modifiers() == true);
    }
  };
}
