
import streamlit as st
import pandas as pd
import base64,random
import time,datetime
#libraries to parse the resume pdf files
from pyresparser import ResumeParser
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
import io,random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
# import pafy #for uploading youtube videos
import plotly.express as px #to create visualisations at the admin session
import nltk
nltk.download('stopwords')
import random
import yt_dlp


def fetch_yt_video(link):
    try:
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            return info.get('title', 'Untitled Video')
    except Exception as e:
        return "Could not fetch title"


def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    """
    Reads a PDF file and extracts all its text content page by page.
    """
    # --- Step 1: Set up the pdfminer tools ---
    resource_manager = PDFResourceManager()
    # Create an in-memory text buffer (a digital notepad).
    fake_file_handle = io.StringIO()
    # Create a converter to turn PDF into text, writing to our in-memory buffer.
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    # Create a page interpreter to process the page content.
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    # --- Step 2: Open and process the file ---
    # Open the PDF file in "read binary" ('rb') mode.
    with open(file, 'rb') as fh:
        # Loop through each page of the PDF.
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            # Process the content of each page.
            page_interpreter.process_page(page)
        
        # --- Step 3: Retrieve the final text ---
        # Get the full string from our in-memory notepad.
        text = fake_file_handle.getvalue()

    # --- Step 4: Clean up and return ---
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🎓 Courses & Certificates Recommendations</h3>', unsafe_allow_html=True)
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

def display_random_video(video_list, section_title):
    """Selects and displays a random video from a list."""
    st.markdown(f'<h1 style="text-align: left; ...">{section_title}</h1>', unsafe_allow_html=True)
    vid_link = random.choice(video_list)
    vid_title = fetch_yt_video(vid_link)
    st.subheader("✅ **" + vid_title + "**")
    st.video(vid_link)




#CONNECT TO DATABASE

connection = pymysql.connect(
    host=st.secrets["database"]["host"],
    user=st.secrets["database"]["user"],
    password=st.secrets["database"]["password"],
    db=st.secrets["database"]["db"]
)
cursor = connection.cursor()

def insert_data(name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp,str(no_of_pages), reco_field, cand_level, skills,recommended_skills,courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

st.set_page_config(
   page_title="Resume Genie",
   page_icon='./Logo/logo1.1.png',
)

# st.markdown('<style>[data-testid=stAppViewContainer]{background-color:white;}.st-emotion-cache-1jicfl2{padding-top:0.5rem;}.st-emotion-cache-zt5igj{left:calc(-3rem);}</style>', unsafe_allow_html=True)
def run():
    img = Image.open('./Logo/logo11.png')
    # img = img.resize()
    st.image(img)
    st.markdown('<h1 style="text-align:left;font-family:Poppins,sans-serif;font-weight:700;font-size:2.5rem;text-shadow:0 0 12px rgba(90,200,250,0.6),3px 3px 6px rgba(0,0,0,0.3),-1px -1px 2px rgba(255,255,255,0.2);letter-spacing:-0.5px;"><span style="background:linear-gradient(90deg, #4F46E5, #00C2FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Resume Genie ✨</span></h1>', unsafe_allow_html=True)
    




    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '[©Developed by ManmitSingh](https://www.linkedin.com/in/manmit-singh-chouhan/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                     (ID INT NOT NULL AUTO_INCREMENT,
                       Name varchar(500) NOT NULL,
                       Email_ID VARCHAR(500) NOT NULL,
                       resume_score VARCHAR(8) NOT NULL,
                       Timestamp VARCHAR(50) NOT NULL,
                       Page_no VARCHAR(5) NOT NULL,
                       Predicted_Field TEXT NOT NULL,      
                       User_level TEXT NOT NULL,           
                       Actual_skills TEXT NOT NULL,        
                       Recommended_skills TEXT NOT NULL,   
                       Recommended_courses TEXT NOT NULL,  
                       PRIMARY KEY (ID));
                     """
    cursor.execute(table_sql)
    cursor.execute(table_sql)
    if choice == 'User':
        st.markdown('<h6 style="text-align: left; color: white; background: linear-gradient(90deg, #4F46E5 0%, #00C2FF 50%, #4F46E5 100%); padding: 8px 12px; border-radius: 6px; font-family: \'Poppins\', sans-serif; font-weight: 600; margin: 8px 0; border: 1px solid rgba(255,255,255,0.3); box-shadow: 0 0 8px rgba(79, 70, 229, 0.4); text-shadow: 0 0 4px rgba(0, 194, 255, 0.3); font-size: 1em;">🧞‍♂️ Let the Genie Reveal Hidden Career Opportunities — Upload Your Resume Now!💨</h6>', unsafe_allow_html=True)
        
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is None and "resume_path" in st.session_state:
            del st.session_state["resume_path"]
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(4)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                # Main Title
                st.markdown('<h1 style="text-align: left; background: linear-gradient(90deg, #4F46E5, #00C2FF); -webkit-background-clip: text; color: transparent; font-family: \'Poppins\', sans-serif; font-weight: 800; font-size: 2.5rem; margin-bottom: 20px; text-shadow: 0 0 12px rgba(124, 58, 237, 0.6), 3px 3px 6px rgba(0, 0, 0, 0.3), -1px -1px 2px rgba(255, 255, 255, 0.2); letter-spacing: -0.5px;">✨ Resume Genie Analysis</h1>', unsafe_allow_html=True)

                # Success Greeting
                st.markdown(f'<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 15px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 20px; font-weight: 600; text-align: left; margin-top: 20px;">🧞‍♂️ Hello <span style="color: #FFE066;">{resume_data["name"]}</span></div>', unsafe_allow_html=True)

                # Subheader
                st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">📄 Your Basic Info</h3>', unsafe_allow_html=True)
                try:
                    # A more robust way to display the info
                    name = resume_data.get('name', 'Not Found')
                    email = resume_data.get('email', 'Not Found')
                    contact = resume_data.get('mobile_number', 'Not Found')
                    pages = resume_data.get('no_of_pages', 'Not Found')
                    
                    st.markdown(f"""<p style='text-align: left; color: #E0E0E0; font-family: Segoe UI, sans-serif;'>
                                    👤 <b>Name:</b> {name}
                                </p>""", unsafe_allow_html=True)
                    
                    st.markdown(f"""<p style='text-align: left; color: #E0E0E0; font-family: Segoe UI, sans-serif;'>
                                    📧 <b>Email:</b> {email}
                                </p>""", unsafe_allow_html=True)
                                
                    st.markdown(f"""<p style='text-align: left; color: #E0E0E0; font-family: Segoe UI, sans-serif;'>
                                    📞 <b>Contact:</b> {contact}
                                </p>""", unsafe_allow_html=True)
                    
                    st.markdown(f"""<p style='text-align: left; color: #E0E0E0; font-family: Segoe UI, sans-serif;'>
                                    📄 <b>Resume pages:</b> {pages}
                                </p>""", unsafe_allow_html=True)
                except:
                    pass


                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 20px; font-weight: 600; text-align: left; margin-top: 20px;">🧑‍🎓 You are at <span style="color: #FFE066;">Fresher</span> level!</div>', unsafe_allow_html=True)

                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 20px; font-weight: 600; text-align: left; margin-top: 20px;">🧑‍🎓 You are at <span style="color: #FFE066;">Intermediate</span> level!</div>', unsafe_allow_html=True)

                elif resume_data['no_of_pages'] >=3:
                    cand_level = "Experienced"
                    st.markdown('<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 20px; font-weight: 600; text-align: left; margin-top: 20px;">🧑‍🎓 You are at <span style="color: #FFE066;">Experienced</span> level!</div>', unsafe_allow_html=True)

                
                # --- Display User's Current Skills ---
                st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🔧 Your Current Skills</h3>', unsafe_allow_html=True)
                keywords = st_tags(label='', text='See our skills recommendation below', value=resume_data['skills'], key='1')
                
                # --- Skill-based Recommendation Logic ---
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator', 'illustrator',
                                'adobe after effects', 'after effects', 'adobe premier pro', 'premier pro', 'adobe indesign',
                                'indesign', 'wireframe', 'solid', 'grasp', 'user research', 'user experience']
                
                reco_field = ''
                rec_course = ''
                
                # 1. Initialize scores for each field
                scores = {'Data Science': 0, 'Web Development': 0, 'Android Development': 0, 'IOS Development': 0, 'UI-UX Development': 0}
                
                # 2. Loop through ALL skills and update scores
                for skill in resume_data['skills']:
                    skill_lower = skill.lower()
                    if skill_lower in ds_keyword:
                        scores['Data Science'] += 1
                    if skill_lower in web_keyword:
                        scores['Web Development'] += 1
                    if skill_lower in android_keyword:
                        scores['Android Development'] += 1
                    if skill_lower in ios_keyword:
                        scores['IOS Development'] += 1
                    if skill_lower in uiux_keyword:
                        scores['UI-UX Development'] += 1
                
                # 3. Find the field with the highest score
                # Check if there are any matches at all
                if max(scores.values()) > 0:
                    reco_field = max(scores, key=scores.get)
                
                    # 4. Display the recommendation for the winning field
                    st.markdown(f'<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 12px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 18px; font-weight: 600; text-align: center; margin-top: 20px;">🔍 Our analysis says you are looking for <span style="color: #FFE066;">{reco_field}</span> Jobs!</div>', unsafe_allow_html=True)
                
                    if reco_field == 'Data Science':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">✨ Recommended Skills For You</h3>', unsafe_allow_html=True) 
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='', text='Recommended skills generated from System', value=recommended_skills, key='2')
                        rec_course = course_recommender(ds_course)
                
                    elif reco_field == 'Web Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True) 
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='', text='Recommended skills generated from System', value=recommended_skills, key='3')
                        rec_course = course_recommender(web_course)
                
                    elif reco_field == 'Android Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True)
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='', text='Recommended skills generated from System', value=recommended_skills, key='4')
                        rec_course = course_recommender(android_course)
                
                    elif reco_field == 'IOS Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True)
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='', text='Recommended skills generated from System', value=recommended_skills, key='5')
                        rec_course = course_recommender(ios_course)
                
                    elif reco_field == 'UI-UX Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True)
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='', text='Recommended skills generated from System', value=recommended_skills, key='6')
                        rec_course = course_recommender(uiux_course)
                else:
                    # Handle the case where no relevant skills were found
                    st.warning("Could not determine a career field based on the skills provided in the resume.")

                
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)

                ### Resume writing recommendation
                # st.subheader("**Resume Tips & Ideas💡**")
                # st.markdown('<h3 ...></h3>', unsafe_allow_html=True)
                st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">💡 Resume Tips & Ideas</h3>', unsafe_allow_html=True)
                resume_score = 0
                
                # Create a list of checks to perform. Each item is a tuple containing:
                # (keywords_to_check, section_name, success_message, failure_message)
                checks = [
                    (['Objective'], 'Objective', '[+] Awesome! You have added your Career Objective', '[-] Please add your career objective...'),
                    (['Declaration'], 'Declaration', '[+] Awesome! You have added the Declaration', '[-] Please add a Declaration at the end...'),
                    (['Hobbies', 'Interests'], 'Hobbies/Interests', '[+] Awesome! You have added your Hobbies', '[-] Consider adding a Hobbies section...'),
                    (['Achievements'], 'Achievements', '[+] Awesome! You have added your Achievements', '[-] Please add any Achievements...'),
                    (['Projects'], 'Projects', '[+] Awesome! You have added your Projects', '[-] Please add any Projects you have worked on...')
                ]
                
                for keywords, section_name, success_msg, failure_msg in checks:
                    # Check if any of the keywords for the current section exist in the resume
                    if any(keyword in resume_text for keyword in keywords):
                        resume_score += 20
                        st.markdown(f'<h5 style="text-align: left; color: #00FFE0;">{success_msg}</h5>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<h5 style="text-align: left; color: #FFFFFF;">{failure_msg}</h5>', unsafe_allow_html=True)
                # st.subheader("**Resume Score📝**")
                st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">Resume Score📝</h3>', unsafe_allow_html=True)
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #FF5C5C; /* softer and brighter red for better dark mode visibility */
                            border-radius: 8px; /* smooth rounded progress bar */
                        }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                my_bar = st.progress(0)
                for i in range(resume_score):
                    time.sleep(0.05)  # Make it a bit faster
                    my_bar.progress(i + 1)
                
                # We already have the score in the 'resume_score' variable
                # st.markdown(f'<div>📝 ?Your Resume Writing Score: <span>{resume_score}</span></div>', unsafe_allow_html=True)                # st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.markdown(f'<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 20px; font-weight: 600; text-align: left; margin-top: 20px;">📝 Your Resume Writing Score: <span style="color: #FFE066;">{resume_score}</span></div>', unsafe_allow_html=True)
                st.markdown('<div style="background: linear-gradient(90deg, #FFA500, #FF6347); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 16px; font-weight: 600; text-align: left; margin-top: 10px;">ℹ️ Note: This score is calculated based on the content that you have in your Resume.</div>', unsafe_allow_html=True)
                st.balloons()

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                              str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                              str(recommended_skills), str(rec_course))


                # Display a random resume video
                display_random_video(resume_videos, "🎥 Bonus Video for Resume Writing Tips💡")
               
                # Display a random interview video
                display_random_video(interview_videos, "🎥 Bonus Video for Interview Tips💡")
               
                connection.commit()

            
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        ## Admin Sidem
        st.markdown('<h6 style="text-align: left; color: white; background: linear-gradient(90deg, #4F46E5, #00C2FF); padding: 10px 12px; border-radius: 8px; font-family: \'Poppins\', sans-serif; font-weight: 600; margin: 8px 0; border: none; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); font-size: 1em;">✨ Welcome to Admin Dashboard</h6>', unsafe_allow_html=True)
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == st.secrets["admin"]["user"] and ad_password == st.secrets["admin"]["password"]:
                st.success("Welcome Admin!")
                
                # --- Simplified Data Fetching ---
                # Fetch data directly from the database
                cursor.execute('''SELECT * FROM user_data''')
                data = cursor.fetchall()
                
                # Define column names for the DataFrame
                column_names = ['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page', 
                                'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills', 
                                'Recommended Course']

                # Create DataFrame directly from the fetched data
                df = pd.DataFrame(data, columns=column_names)
                
                # Display the data table and download link
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                
                # --- Chart Plotting ---
                # The DataFrame 'df' is already clean and ready for plotting
                
                ## Pie chart for predicted field recommendations
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                field_counts = df['Predicted Field'].value_counts()
                fig1 = px.pie(values=field_counts.values, names=field_counts.index, title='Predicted Field according to Skills')
                st.plotly_chart(fig1)

                ### Pie chart for User's Experienced Level
                st.subheader("**Pie-Chart for User's Experienced Level**")
                level_counts = df['User Level'].value_counts()
                fig2 = px.pie(values=level_counts.values, names=level_counts.index, title="User's Experience Level")
                st.plotly_chart(fig2)

            else:
                st.error("Wrong ID & Password! Please try again.")
       
run()