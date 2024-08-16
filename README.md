# Pokemon Database/Team Builder

A small database for Pokemon

## Prerequisites

Make sure you have Git and Python installed on your machine:

- [Git](https://git-scm.com/) for version control.
- [Python 3.x](https://www.python.org/downloads/)
- [Virtualenv](https://virtualenv.pypa.io/en/latest/) to create Python environments.

## Installation

Follow these steps to download and set up the project locally:

1. **Clone the repository**  
   Click on the green 'Code' button and copy the SSH url. Open your terminal, type 'git clone' then paste the url. Alternatively, run the following command:

   git clone https://github.com/Molmstead97/poke_project.git

2. **Navigate to the project directory**
   After cloning, move into the project folder:
      cd poke_project

4. **Create a virtual environment**
   Create a virtual environment to manage dependencies:
      python -m venv venv

   Then activate it:
      On windows:
         venv\Scripts\activate
      On mac:
         source venv/bin/activate

6. **Install dependencies**
   Use 'pip' to install the required packages:
      pip install -r requirements.txt

7. **Run the project**
   Everything should be set up, go ahead and run:
      uvicorn main:app --reload

   Then, open a new tab in your browser and copy this url into the address bar:
      http://127.0.0.1:8000/docs#/

   And that's it! You should have the database and team builder ready to go


