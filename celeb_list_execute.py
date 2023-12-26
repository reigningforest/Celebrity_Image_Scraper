import subprocess

# Specify the path to the Python file you want to execute
file_to_execute = "E:/Projects/file/path.py"

example_celeb_list = ["Beyoncé Knowles","Jackie Chan","Greta Thunberg","Lionel Messi","Deepika Padukone","Samuel L. Jackson","Angela Merkel","Malala Yousafzai",
   "Keanu Reeves","Sofía_Vergara","Trevor Noah","Emma Watson","Manny Pacquiao","Naomi Ōsaka","Shakira","Jeff Bezos","Kim Jong-un","Ellen DeGeneres",
   "Russell Peters","Michelle Obama","Benjamin Netanyahu","Maggie Smith","Elon Musk","Amitabh Bachchan","Usain Bolt","Gisele Bündchen","Pelé",
   "Nelson Mandela","Madonna (entertainer)","Novak Đoković","Serena Williams","Salma Hayek","Justin Trudeau","Morgan Freeman","Victoria Beckham","Park Ji-sung",
   "Rihanna","Arnold Schwarzenegger","Sandra Bullock","Hayao Miyazaki","Sonia Sotomayor","Nadia Murad","Ken Watanabe","Shigeru Miyamoto",
   "Mark Zuckerberg","Michelle Bachelet","David Attenborough","Ma Yun","Cristiano Ronaldo","Oprah Winfrey"]

# test_list = ["Ken Watanabe","Shigeru Miyamoto"]

for input_name in example_celeb_list:
    print(input_name)
    subprocess.run(["python", file_to_execute, input_name])
