# Dashing Growth Curves
Dashing Growth Curves is an open-source web app (http://dashing-growth-curves.ethz.ch/) for the analysis of microbial growth curves.
## Latest release notes
- 2024-01-07 update:
    - added overview plot of all samples to facilitate data exploration
    - added Easy Linear algorithm to options for automated data analysis
    - upgraded to Python 3.12 for improved performance
- 2022-12-15 first release
## How to cite
If you found Dashing Growth Curves useful for your work please cite [Reiter and Vorholt, 2024](https://link.springer.com/article/10.1186/s12859-024-05692-y).
## Questions and Bug reports
Please refer to the issues section and feel free to ask a question.
I can also be found on X @mRetier
## Local installation
Local installation requires basic conding knowledge.
1. Install Git
2. Install Python 3.12
3. Make a new virtual environment and activate it
4. Go to the directory you wish to install Dashing Growth Curves in
5. Download or clone (`git clone https://github.com/mretier/growthdash.git`) the Dashing Growth Curves repository 
6. Install all required python packages from the `requirements.txt` file: `pip install -r requirements.txt`
7. Start the app with `python ./app.py`
8. Open a new browser window and go to `http://0.0.0.0:8050/`, this should start the application which should behave the same way the web version does.
