import subprocess

# Specify the path to the Python file you want to execute
file_to_execute = "E:/Projects/file/path.py"

example_celeb_list = ["Beyoncé Knowles","Jackie Chan","Greta Thunberg"]

# test_list = ["Ken Watanabe","Shigeru Miyamoto"]

for input_name in example_celeb_list:
    print(input_name)
    subprocess.run(["python", file_to_execute, input_name])
