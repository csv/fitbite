import fitbit
from selenium import webdriver
import os, time, random, re, yaml
from optparse import OptionParser

def load_config():
  parser = OptionParser()
  parser.add_option("-c", "--config", dest="config", default='fitbite.yaml',
                  help="yaml-formatted config file")
  (options, args) = parser.parse_args()

  return yaml.safe_load(open(options.config).read())

def authorize_with_fitbit():

  consumer_key = os.getenv('FITBIT_CONSUMER_KEY')
  consumer_secret = os.getenv('FITBIT_CONSUMER_SECRET')
  user_key = os.getenv('FITBIT_USER_KEY')
  user_secret = os.getenv('FITBIT_USER_SECRET')

  return fitbit.Fitbit(consumer_key, consumer_secret, user_key=user_key, user_secret=user_secret)

def determine_calorie_level(fb, config):

  steps = fb.activity_stats()['lifetime']['tracker']['steps']
  steps = 6000
  print "You've taken %d steps today" % steps
  # find possible levels
  levels = config['levels']
  the_calorie_level = levels[0].keys()[0]
  for l in levels:
    calorie_level, step_level = l.keys()[0], l.values()[0]
    if step_level < steps:
      the_calorie_level = calorie_level

  return the_calorie_level

def order_seamless(calorie_level):
  # seamless info
  SEAMLESS_URL = "http://www.seamless.com/"
  SEAMLESS_EMAIL = os.getenv("SEAMLESS_EMAIL")
  SEAMLESS_PASSWORD = os.getenv("SEAMLESS_PASSWORD")

  # setup browser
  browser = webdriver.Chrome()

  # open seamless and login
  browser.get(SEAMLESS_URL)
  browser.find_element_by_id('memberLogin').click()
  time.sleep(5)
  browser.find_element_by_id('username').send_keys(SEAMLESS_EMAIL)
  browser.find_element_by_id('password').send_keys(SEAMLESS_PASSWORD)
  browser.find_element_by_id('corporate_member_submit').click()
  time.sleep(5)
  # navigate to favorite meals
  browser.find_element_by_link_text('Favorite Meals').click()
  time.sleep(5)
  orders = browser.find_elements_by_class_name('action')

  #filter by order:
  orders = [o for o in orders if o.text == 'Order now']

  # filter by caloric content
  possible_orders = [o for o in orders if re.search(".*"+calorie_level+".*", o.find_element_by_tag_name('a').get_attribute('title'))]

  n = len(possible_orders)
  if n==0:
    print "No suitable orders available at this time. It's probably too late to eat anyways!"
    return ""
  elif n==1:
    the_order = possible_orders[0]
  elif n>1:
    the_order = possible_orders[random.sample(range(0,(len(possible_orders)-1)))]

  # select the order
  the_order.click()
  time.sleep(5)

  # proceed to checkout
  browser.find_element_by_id('FormAction').click()
  time.sleep(5)
  # browser.find_element_by_id('FormAction').click()

  return "Check %s to see what you ordered!" % SEAMLESS_PASSWORD

if __name__ == '__main__':

  config = load_config()
  fb = authorize_with_fitbit()
  calorie_level = determine_calorie_level(fb, config)
  print order_seamless(re.sub("_", " ", calorie_level))
