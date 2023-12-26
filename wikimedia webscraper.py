from lxml import html
import aiohttp
import asyncio
import aiofiles
import os
import pandas as pd
import regex as re
import urllib.parse
import sys

from pandas.io.formats import excel
excel.ExcelFormatter.header_style = None

# NOTE
# all categories will be saved into storeDirectory on completion
## Use asyncio to allow for coroutines to be established. That is, allowing for functions to run concurrently.
## This is important for allowing other less time intensive functions to run while other more time intensive functions are running
## Example: I/O (in/out) bound tasks such as image downloading or fetching webpages takes a large amount of time.
## So while fetch_images is running, the program can continue to run fetch_pages to get category pages.
## The program must wait for the list of image urls to be gathered from each subcategory page, but then while the images are downloading,
### the program can start another image downloads.


# ------------------------------------------------------
# TODO: Rename images to be Name_ImageNumber_date
# TODO: make this run on loop for a list of patients
# new_celeb_list = []
# for i in celeb_list:
#   new_celeb_list.append(i.replace(" ", "_"))

# ------------------------------------------------------

input_name = "Ken Watanabe"
# storeDirectory = "C:/Users/jh1083/Downloads/"
storeDirectory = 'C:/Users/johnh/Downloads/'
# storeDirectory = '//Smbgpa/airo_mgb$/Data/Fridolin_Haugg/Healthy celebrity images/'
checkForCategories = True
checkForName = True
categoryNameSkip = ["Signature", "signature", "Art", "art",
                    "Caricature", "caricature", "Chart", "chart",
                    "Hollywood", "hollywood", "Star", "star",
                    "Logo", "logo", "Film", "film", "Video", "video",
                    "Animal", "animal", "Shirt", "shirt",
                    "Figure", "figure", "Character", "character"]





def category_skip(input_str, categoryNameSkip):
    for word in categoryNameSkip:
        if word in input_str:
            return False
    return True

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
        if checkForName:
          if input_name in category.text and category_skip(category.text, categoryNameSkip):
            print(category.text)
            categoryTasks.append(asyncio.ensure_future(fetch_images(session, 'https://commons.wikimedia.org' + category.attrib['href'])))
            checkedCategories.append(category)
            print('Found category', category.attrib['href'])
        else:
          categoryTasks.append(asyncio.ensure_future(fetch_images(session, 'https://commons.wikimedia.org' + category.attrib['href'])))
          checkedCategories.append(category)
          print('Found category', category.attrib['href'])

  if (len(images) > 0):
    totalImages += len(images)
    print("Found", len(images), "images")
    #download images for each category
    for image in images:
      cat = full_name
      tasks.append(asyncio.ensure_future(fetch_page(session, 'https://commons.wikimedia.org' + image.attrib['href'], cat)))

  global completed
  completed += 1

async def main(loop):
  global completedImages
  global url
  global full_name

  url = 'https://commons.wikimedia.org/wiki/Category:' + input_name.replace(" ", "_")
  full_name = url.split('Category:')[1]

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
      print(page[0])
      #timeout error
      if(page == False):
        continue

      cat = page[0]
      source = page[1]

      #print(cat, source.xpath('*//div[@class="fullImageLink"]//img')[0].attrib['src'])
      try:
        imgURL = source.xpath('*//div[@class="fullImageLink"]//img')[0].attrib['src']
        parsed_url = urllib.parse.urlparse(imgURL)
        filename = urllib.parse.unquote(parsed_url.path.split('/')[-1].split('?')[0])
        filename = re.sub('[^a-zA-Z0-9_.-]+', '_', filename)
        # filename = re.sub('[/:*?<>,|#“”\']', '', filename).replace('\\', '')

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

      except Exception as e_1:
        imgURL = None
        print(f"Error: {e_1} - Skipping: {imgURL}")

      print(filename)
      print("------------------------------------------")
      
      #Save images into category folders
      try:
        async with session.get(imgURL) as resp:
          # HTTP status code 200: OK - standard response for a successful HTTP request.
          if resp.status == 200:
            if(os.path.isdir(storeDirectory + full_name + '/') == False):
              os.mkdir(storeDirectory + full_name + '/')

            if(os.path.isdir(storeDirectory + full_name + '/' + full_name + '/') == False):
              os.mkdir(storeDirectory + full_name + '/' +  full_name + '/')
            
            if os.path.exists(storeDirectory + full_name + '/' + full_name + '/' + filename):
              print("file exists")
            else:
              f = await aiofiles.open(storeDirectory + full_name + '/' + full_name + '/' + filename, mode='wb')
              await f.write(await resp.read())
              await f.close()
            completedImages += 1
            print(completedImages, '/', totalImages)
          else:
            print("failed to download")
      except Exception as e_2:
        print(f"Error: {e_2} - Skipping: {imgURL}")
      
        
  df_1.to_excel(storeDirectory + full_name + '/' + full_name + ".xlsx")
  print(df_1)
  print("Program successful and complete")

# def run_async_loop(iterations):
#   print('running loop')
#   for i in range(iterations):
      
#   print('run ended')

#main event loop
if __name__ == "__main__":
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

  if len(sys.argv) > 1:
      input_name = sys.argv[1]
      
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main(loop))



