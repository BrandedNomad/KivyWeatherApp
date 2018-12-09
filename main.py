# Importing all the relevant modules
import kivy
import requests
kivy.require('1.10.1')
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, ListProperty
from kivy.network.urlrequest import UrlRequest
from kivy.uix.listview import ListItemButton
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
import json
from datetime import datetime
from kivy.graphics import Line
from kivy.graphics import Point
from html.parser import HTMLParser


# @Description: LocationForm creates the layout for the weather apps
# @Inherits: Inherits from BoxLayout
class LocationForm(BoxLayout):
    search_input = ObjectProperty()  # To get the user input from the search box
    search_result = ObjectProperty()  # Creates an object that will be used ot populate the listView
    popup = None

    # @description: a fucntion that formats the user input as a url request and then requests the data from the api
    # @param: None
    # @Return None
    def search_location(self):
        search_template = "http://api.openweathermap.org/data/2.5/" + \
            "find?q={}&type=like&appid=ce30b7c9b23fa7d6c1a110f115033c3d"  # Creates a url template
        # inserts the user_input into the url template
        search_url = search_template.format(self.search_input.text)
        # Callback fucntion that makes url requests and then calls the found location function to handle the data returned
        request = UrlRequest(search_url, on_success=self.found_location, on_error=self.failed)
        self.popup = Popup(title='Request Sent', content=Label(text="Loading..."),
                           size_hint=(None, None), size=(400, 400), auto_dismiss=True)
        self.popup.open()

    def failed(self, request, data):
        self.popup.dismiss()
        self.popup = Popup(title='Request Failed!', content=Label(text="Connection error!...Try again later"),
                           size_hint=(None, None), size=(400, 400), auto_dismiss=True)
        self.popup.open()
    # @description: a function that recieves data from api and formats it for display in ListView
    # @param: request -
    # @param: data - a json dictionary object returned from the api that contains the results of the request
    # @return: Sets the listView to the data received

    def found_location(self, request, data):
        # Ternary that checks of object is a dictionary if not then load it as a json object to make it compatible with python
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        # list comprehension that reformat data into: city name (country) and stores it as a list item
        # print(data)
        cities = ["{} ({})".format(d['name'], d['sys']['country']) for d in data['list']]
        if len(cities) == 0:  # input validation, that displays no cities found when input is not valid
            cities = ["New York US"]
        # Sets the empty list in search results to the newly formated list of results named cities obtained from api
        self.search_result.item_strings = cities
        self.search_result.adapter.data.clear()  # Clear any data form previous searches
        self.search_result.adapter.data.extend(cities)  # extend the list with new data
        self.search_result._trigger_reset_populate()  # updates display when data changes
        self.popup.dismiss()


class LocationButton(ListItemButton):
    pass


class CurrentWeather(BoxLayout):
    location = StringProperty("New York US")
    conditions = StringProperty()
    temp = NumericProperty()
    temp_max = NumericProperty()
    temp_min = NumericProperty()
    conditions_image = StringProperty()

    def update_weather(self):

        weather_template = "http://api.openweathermap.org/data/2.5/" + \
            "weather?q={}&units=metric&appid=ce30b7c9b23fa7d6c1a110f115033c3d"  # Creates a url template

        # Reformats the location string by removing the brackets and entering a ,
        location = self.location
        n = [i for i in location if i != "("]
        x = [i for i in n if i != ")"]
        y = ''.join(x)
        z = y.split(" ")
        clean_location = ','.join(z)
        # inserts the user_input into the url template
        weather_url = weather_template.format(clean_location)
        # Callback fucntion that makes url requests and then calls the found location function to handle the data returned
        request = UrlRequest(weather_url, self.found_weather)

    def found_weather(self, request, data):
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        print(data)
        self.conditions = data['weather'][0]['description']
        self.conditions_image = "http://openweathermap.org/img/w/{}.png".format(
            data['weather'][0]['icon'])
        self.temp = data['main']['temp']
        self.temp_max = data['main']['temp_max']
        self.temp_min = data['main']['temp_min']


class WeatherRoot(BoxLayout):
    current_weather = ObjectProperty()
    locations = ObjectProperty()
    location_list = ObjectProperty()
    forecast = ObjectProperty()

    def __init__(self, **kwargs):
        super(WeatherRoot, self).__init__(**kwargs)
        self.store = JsonStore("weather_store.json")
        if(self.store.exists("locations")):
            current_location = self.store.get("locations")["current_location"]
            self.show_current_weather(current_location)

    def show_current_weather(self, location):
        self.clear_widgets()
        if self.current_weather is None:
            self.current_weather = CurrentWeather()
        if self.locations is None:
            self.locations = Factory.Locations()
            if(self.store.exists("locations")):
                locations = self.store.get("locations")["locations"]
                self.locations.location_list.adapter.data.extend(locations)
        if location is not None:
            self.current_weather.location = location
            if location not in self.locations.location_list.adapter.data:
                self.locations.location_list.adapter.data.append(location)
                self.locations.location_list._trigger_reset_populate()
                self.store.put(
                    "locations", locations=self.locations.location_list.adapter.data, current_location=location)

        else:
            self.current_weather.location = "New York"
            self.current_weather.update_weather()

        self.current_weather.update_weather()
        self.add_widget(self.current_weather)

    def show_location(self):
        self.clear_widgets()
        self.add_widget(self.locations)

    def show_location_form(self):
        self.clear_widgets()
        self.current_weather.conditions = ""
        self.current_weather.temp = 00
        self.current_weather.temp_max = 00
        self.current_weather.temp_min = 00
        self.current_weather.conditions_image = ""
        self.add_widget(LocationForm())

    def clear_location_list(self):
        self.locations.location_list.adapter.data = []
        self.show_location()
        self.store.put("locations", locations=[], current_location=None)

    def show_forecast(self, location=None):
        self.clear_widgets()
        if self.forecast is None:
            self.forecast = Factory.Forecast()
        if location is not None:
            self.forecast.location = location
        self.forecast.update_weather()
        self.add_widget(self.forecast)


class Forecast(BoxLayout):
    location = StringProperty("New York")
    forecast_container = ObjectProperty()

    def update_weather(self):
        weather_template = "http://api.openweathermap.org/data/2.5/forecast?q={}&units=metric&cnt=3&appid=ce30b7c9b23fa7d6c1a110f115033c3d"
        # Reformats the location string by removing the brackets and entering a ,
        location = self.location
        n = [i for i in location if i != "("]
        x = [i for i in n if i != ")"]
        y = ''.join(x)
        z = y.split(" ")
        clean_location = ','.join(z)
        print(clean_location)
        # inserts the user_input into the url template
        weather_url = weather_template.format(clean_location)
        # Callback fucntion that makes url requests and then calls the found location function to handle the data returned
        request = UrlRequest(weather_url, self.found_forecast, on_error=self.failed)

    def found_forecast(self, request, data):
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        print(data)
        self.forecast_container.clear_widgets()
        for day in data['list']:
            label = Factory.ForecastLabel()
            Label.condition = day['weather'][0]['description']
            label.conditions_image = "http://openweathermap.org/img/w/{}.png".format(
                day['weather'][0]['icon'])
            label.temp_max = day['main']['temp_max']
            label.temp_max = day['main']['temp_min']
            label.date = datetime.utcfromtimestamp(day['dt']).strftime(" %a %b %d")
            self.forecast_container.add_widget(label)

    def failed(self, request, data):
        self.popup.dismiss()
        self.popup = Popup(title='Request Failed!', content=Label(text="Connection error!...Try again later"),
                           size_hint=(None, None), size=(400, 400), auto_dismiss=True)
        self.popup.open()


# @description: A class that creates the user interface using the location form layout
# @inherit: Inherits from the App class


class WeatherApp(App):
    def build(self):
        return WeatherRoot()


# Starts the app
if __name__ == "__main__":
    WeatherApp().run()
