# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import jinja2
import webapp2
from google.appengine.api import urlfetch
import json

from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),"templates")
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
	autoescape = True)

def static_map_marker(points):
    url = "https://maps.googleapis.com/maps/api/staticmap?size=500x400&"
    x="P"
    for point in points:
        url += "markers=label:"+x+"|"+str(point[0])+","+str(point[1])+"&"
        x = "H"
    return url+"key=AIzaSyD6-ghbdBFvbnPNVxqRVtFPf_mAqjUsWYM"

def get_value():
    f = open("arduino_result.txt", "r")
    value = f.read()
    return int(value)

def send_sms(to_num, address, url):
    from twilio.rest import Client

    account_sid = "sid"
    auth_token  = "token"

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to=to_num, 
        from_="+442380000395",
        body="""There's an accident at the following address:\n%s\nWe hereby request you to send an ambulance at the above address.\n
        Thank you"""%address,
        media_url=url)

    print(message.sid)

def get_nearby_hospital(location):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s&rankby=distance&types=hospital&types=health&key=AIzaSyD6-ghbdBFvbnPNVxqRVtFPf_mAqjUsWYM"%location
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    hdr = {'User-Agent':user_agent}
    req = urlfetch.fetch(url, method='POST' , headers=hdr)
    content = req.content
    dic = json.loads(content)
    if content:
        return (str(dic['results'][0]['place_id']), str(dic['results'][0]['name']))

def get_number(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyD6-ghbdBFvbnPNVxqRVtFPf_mAqjUsWYM"%place_id
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    hdr = {'User-Agent':user_agent}
    req = urlfetch.fetch(url, method='POST' , headers=hdr)
    content = req.content
    if content:
        dic = json.loads(content)
        return str(dic['result']['formatted_phone_number'])

def get_cords_hospital(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=AIzaSyD6-ghbdBFvbnPNVxqRVtFPf_mAqjUsWYM"%place_id
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    hdr = {'User-Agent':user_agent}
    req = urlfetch.fetch(url, method='POST' , headers=hdr)
    content = req.content
    if content:
        dic = json.loads(content)
        return (dic['result']['geometry']['location']['lat'], dic['result']['geometry']['location']['lng'])

def get_cords():
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    hdr = {'User-Agent':user_agent} 
    url = "https://www.googleapis.com/geolocation/v1/geolocate?key=AIzaSyD6-ghbdBFvbnPNVxqRVtFPf_mAqjUsWYM"
    content = None
    req = urlfetch.fetch(url, method='POST' , headers=hdr)
    content = req.content
    content = json.loads(content)
    if content:
        dic = (content['location']['lat'],content['location']['lng'])
        return dic

def get_address(location):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s&key=AIzaSyD6-ghbdBFvbnPNVxqRVtFPf_mAqjUsWYM"%location
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    hdr = {'User-Agent':user_agent}
    content = None
    req = urlfetch.fetch(url, method='POST' , headers=hdr)
    content = req.content
    dic = json.loads(content)
    if content:
        return dic['results'][0]['formatted_address']
        
class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)

	def render_str(self,template,**params):
		t=jinja_env.get_template(template)
		return t.render(params)

	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

class MainPage(Handler):
    def get(self):
        cords = get_cords()
        lat = cords[0]
        lon = cords[1]
        hospital_place_id = get_nearby_hospital(str(lat)+","+str(lon))[0]
        hospital_name = get_nearby_hospital(str(lat)+","+str(lon))[1]
        all_cords = [cords,get_cords_hospital(hospital_place_id)]
        number = get_number(hospital_place_id)
        address = get_address(str(lat)+","+str(lon))
        static_url = static_map_marker(all_cords)
        #send_sms(number, address, static_url)  FOR SENDING SMS TO NEAREST HOSPITAL
        self.render("front.html",url=static_url,hospital_name=hospital_name)
                
app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)