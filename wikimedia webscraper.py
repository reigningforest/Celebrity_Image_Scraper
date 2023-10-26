import shutil
from lxml import etree
from lxml import html
import aiohttp
import asyncio
import aiofiles
# import nest_asyncio # only for google colab
import os
import pandas as pd

from pandas.io.formats import excel
excel.ExcelFormatter.header_style = None

#fix for running in colab
# nest_asyncio.apply()

#all categories will be compressed into storeDirectory + download.zip on completion

#ONLY CHNAGE THIS
url = 'https://commons.wikimedia.org/wiki/Category:Hayao_Miyazaki'
storeDirectory = 'C:/Users/johnh/Downloads/test/'
# storeDirectory = 'E:/Projects/Frido/results yeah/'
checkForCategories = False

#DON'T CHANGE
df_1 = pd.DataFrame({"image_name":[],
                     "image_url":[],
                     "date_taken":[],
                     "date_alt":[],
                     "desc":[]})
tasks = []
categories = 0
categoryTasks = []
checkedCategories = []
completed = -1
totalImages = 0
completedImages = 0

async def fetch_page(session, url, cat = ''):
  try:
    async with session.get(url) as resp:
      source = await resp.text()

      dom = html.fromstring(source)

      return [cat, dom]
  except asyncio.TimeoutError or aiohttp.ClientConnectorError:
    #print('Timeout')
    return False

async def fetch_images(session, url):
  global totalImages

  dom = await fetch_page(session, url)
  #timeout error
  if dom == False:
    return
  images = dom[1].xpath('*//div[@class="thumb"]//a')
  subcategories = dom[1].xpath('*//div[@class="CategoryTreeItem"]//a')

  if(len(subcategories) > 0 and checkForCategories):
    for category in subcategories:
      if(category not in checkedCategories):
        categoryTasks.append(asyncio.ensure_future(fetch_images(session, 'https://commons.wikimedia.org' + category.attrib['href'])))
        checkedCategories.append(category)
        print('Found category', category.attrib['href'])

  if (len(images) > 0):
    totalImages += len(images)
    print("Found", len(images), "images")
    #download images for each category
    for image in images:
      cat = url.split('Category:')[1]
      tasks.append(asyncio.ensure_future(fetch_page(session, 'https://commons.wikimedia.org' + image.attrib['href'], cat)))

  global completed
  completed += 1

async def main(loop):
  global url
  global completedImages

  async with aiohttp.ClientSession(loop=loop) as session:
    await fetch_images(session, url)

    #fix to resolve finding all categories first
    while True:
      await asyncio.gather(*categoryTasks)

      #check if images have been found on all category pages
      if(completed == len(categoryTasks)):
        break

    pages = await asyncio.gather(*tasks)
    for page in pages:
      print(page)
      #timeout error
      if(page == False):
        continue

      cat = page[0]
      source = page[1]

      #print(cat, source.xpath('*//div[@class="fullImageLink"]//img')[0].attrib['src'])
      imgURL = source.xpath('*//div[@class="fullImageLink"]//img')[0].attrib['src']

      filename = imgURL.split('/')[-1].split('?')[0]

      dateURL = source.xpath('//*[@id="mw-imagepage-content"]/div/div/table/tbody/tr[2]/td[2]/time')
      dateURL_alt = source.xpath('//*[@id="mw-imagepage-content"]/div/div/table/tbody/tr[2]/td[2]')
      descURL = source.xpath('//*[@id="mw-imagepage-content"]/div/div/table/tbody/tr[1]/td[2]')

      # Check if the cell element was found
      if dateURL:
        datetext = dateURL[0].text
      else:
        datetext = "Date not found"
      # print(datetext)

      if dateURL_alt:
        datetext_alt = dateURL_alt[0].text_content().strip().replace("\n", " ")
      else:
        datetext_alt = "Date Alt not found"
      # print(datetext_alt)

      if descURL:
        desctext = descURL[0].text_content().strip().replace("\n", " ")
      else:
        desctext = "Description not found"
      # print(desctext)
      
      new_row = {"image_name":filename,
                 "image_url":imgURL,
                 "date_taken":datetext,
                 "date_alt":datetext_alt,
                 "desc":desctext}

      df_1.loc[len(df_1)] = new_row

      print(filename)
      print("------------------------------------------")
      
      #TODO: save images into category folders
      async with session.get(imgURL) as resp:
        if resp.status == 200:
            if(os.path.isdir(storeDirectory + cat + '/') == False):
              os.mkdir(storeDirectory + cat + '/')

            f = await aiofiles.open(storeDirectory + cat + '/' + filename, mode='wb')
            await f.write(await resp.read())
            await f.close()
            completedImages += 1
            print(completedImages, '/', totalImages)
  df_1.to_excel(storeDirectory + url.split('Category:')[1] + ".xlsx")
  print(df_1)

  #create zip file to download
  # shutil.make_archive(storeDirectory + 'download', 'zip', storeDirectory)

#main event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))