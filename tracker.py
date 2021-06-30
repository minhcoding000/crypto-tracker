import sys
sys.path.insert(1, "./lib")

import os
import logging
import time
import epd2in7
from PIL import Image, ImageOps ,ImageDraw, ImageFont
import requests
import RPi.GPIO as GPIO
import numpy as np
import matplotlib.pyplot as plt

dirname = os.path.dirname(__file__)
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')

epd = epd2in7.EPD()
epd.init()
logging.info("Clear...")
epd.Clear()

def getHistoricalData(coin):
  print("Getting Data")
  days_ago = 7
  endtime = int(time.time())
  starttime = endtime - 60*60*24*days_ago
  endtimesecs = endtime
  starttimesecs = starttime
  geckourlhistorical = "https://api.coingecko.com/api/v3/coins/"+coin+"/market_chart/range?vs_currency=usd&from="+str(starttimesecs) +  "&to=" + str(endtimesecs)
  print(geckourlhistorical)
  rawtimeseries = requests.get(geckourlhistorical).json()
  print("Got price for the last "+ str(days_ago) +" days from CoinGecko.")
  print(rawtimeseries)
  timeseriesarray = rawtimeseries['prices']
  timeseriesstack = []

  length = len(timeseriesarray)
  print("Length: "+str(length))
  i = 0
  while i < length:
    timeseriesstack.append(float (timeseriesarray[i][1]))
    i+=1
  #print(timeseriesstack)
  return timeseriesstack

def makeChart(pricestack):
  print("Making chart")
  x = pricestack - np.mean(pricestack)
  fig, ax = plt.subplots(1,1,figsize=(15,4.5))
  plt.plot(x, color='k', linewidth=6)
  for k,v in ax.spines.items():
    v.set_visible(False)
  ax.set_xticks([])
  ax.set_yticks([])
  ax.axhline(c='k', linewidth=4, ls='-.')
  #Convert image.png into image.bmp and save that 
  plt.savefig(os.path.join(picdir,'chart.png'), dpi=17)
  imgcht = Image.open(os.path.join(picdir,'chart.png'))
  file_out = os.path.join(picdir,'chart.bmp')
  imgcht.save(file_out)
  plt.clf()
  ax.cla()

def getPrice(coin,fiat):
  geckourl = "https://api.coingecko.com/api/v3/coins/markets?vs_currency="+fiat+"&ids="+coin
  print(geckourl)
  rawData = requests.get(geckourl).json()
  liveprice = rawData[0]
  currentPrice = float(liveprice['current_price'])
  print(currentPrice)
  return currentPrice

def getPercentChange(pricestack):
  percentChange = round(((pricestack[-1] - pricestack[0]) / pricestack[0]) * 100,2)
  print("Percent Change: " + str(percentChange) + "%")
  return percentChange

def initkeys():
  key1 = 5
  key2 = 6
  key3 = 13
  key4 = 19
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(key1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(key2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(key3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(key4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  keys = [key1,key2,key3,key4]
  return keys

def printToDisplay(string,price,percentChange):
  logging.info("Drawing to the screen...")
  Himage = Image.new('1', (epd.height, epd.width), 255) #255:clear the frame
  #Aimage = Image.new('1', (epd.height, epd.width), 255
  draw = ImageDraw.Draw(Himage)
  font = ImageFont.truetype('/usr/share/fonts/truetype/BebasNeue-Regular.ttf',30)
  font2 = ImageFont.truetype('/usr/share/fonts/truetype/BebasNeue-Regular.ttf',35)
  font3 = ImageFont.truetype('/usr/share/fonts/truetype/Montserrat-Regular.ttf',15) 
  #Draw name of coin
  draw.text((10,10), string, font = font2, fill = 0)
  #Draw price of coin in USD
  if price:
    p = "$" + str(price)
    draw.text((150,10), p, font = font, fill = 0)
  #Draw percent change
  percentChangeDuration = "7 Day: " + str(percentChange) + "%"
  draw.text((150,40),percentChangeDuration, font = font3, fill = 0)
  #Draw chart of coin
  chartbitmap = Image.open(os.path.join(picdir,'chart.bmp'))
  Himage.paste(chartbitmap,(0,75))

  epd.display(epd.getbuffer(Himage))

def handleBtnPress():
  printToDisplay("Hello, World!")

# set up the buttons on the epaper
#printToDisplay("Hello, world!")
thekeys = initkeys()
lastfetch = 0
curCoin = " "
while True:
# poll key states
  key1state = GPIO.input(thekeys[0])
  key2state = GPIO.input(thekeys[1])
  key3state = GPIO.input(thekeys[2])
  key4state = GPIO.input(thekeys[3])
  if key1state == False:
    print("Bitcoin")
    price = getPrice('bitcoin','usd')
    pricestack = getHistoricalData("bitcoin")
    makeChart(pricestack)
    percentChange = getPercentChange(pricestack)
    printToDisplay("bitcoin", price, percentChange)
    lastfetch = time.time()
    curCoin = "bitcoin"
    time.sleep(1)
  if key2state == False:
    print("Ethereum")
    price = getPrice('ethereum','usd')
    pricestack = getHistoricalData("ethereum")
    makeChart(pricestack)
    percentChange = getPercentChange(pricestack)
    printToDisplay("ethereum", price, percentChange)
    lastfetch = time.time()
    curCoin = "ethereum"
    time.sleep(1)
  if key3state == False:
    print("Tether")
    price = getPrice('tether','usd')
    pricestack = getHistoricalData("tether")
    makeChart(pricestack)
    percentChange = getPercentChange(pricestack)
    printToDisplay("tether", price, percentChange)
    lastfetch = time.time()
    curCoin = "tether"
    time.sleep(1)
  if key4state == False:
    print("Doge")
    price = getPrice('dogecoin','usd')
    pricestack = getHistoricalData("dogecoin")
    makeChart(pricestack)
    percentChange = getPercentChange(pricestack)
    printToDisplay("dogecoin", price, percentChange)
    lastfetch = time.time()
    curCoin = "dogecoin"
    time.sleep(1)
  if time.time() - lastfetch > 180 and curCoin != " ":
    print(curCoin)
    price = getPrice(curCoin,'usd')
    pricestack = getHistoricalData(curCoin)
    makeChart(pricestack)
    percentChange = getPercentChange(pricestack)
    printToDisplay(curCoin, price, percentChange)
    time.sleep(1)
    lastfetch = time.time()
    
