import streamlit as st
import pandas as pd
import base64, random
import time, datetime

from PIL import Image
import pymysql
import plotly.express as px

import nltk
from nltk.corpus import stopwords
nltk.download("stopwords")

import re
import fitz  # PyMuPDF
import spacy
import yt_dlp

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

from Courses import (
    ds_course, web_course, android_course,
    ios_course, uiux_course, resume_videos, interview_videos
)

st.set_page_config(
   page_title="Resume Genie",
   page_icon='./Logo/logo1.1.png',
)



# -------- Extract full text from PDF --------
def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text


# -------- Extract Name, Email, Phone --------
def extract_basic_details(text):
    # Email
    email = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    email = email[0] if email else "Not Found"

    # Phone
    phone = re.findall(r"\+?\d[\d\s\-]{7,15}", text)
    phone = phone[0] if phone else "Not Found"

    # Name (very simple, works most cases)
    lines = text.split("\n")
    name = lines[0].strip() if len(lines[0]) < 40 else "Not Found"

    return name, email, phone


# -------- Extract skills --------
def extract_skills(text, skill_keywords):
    text_lower = text.lower()
    found_skills = [skill for skill in skill_keywords if skill.lower() in text_lower]
    return ", ".join(found_skills) if found_skills else "Not Found"


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

@st.cache_resource
def get_connection():
    return pymysql.connect(
        host=st.secrets["database"]["host"],
        port=int(st.secrets["database"]["port"]),
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        db=st.secrets["database"]["db"]
    )
connection = get_connection()
cursor = connection.cursor()


def insert_data(name, email, contact, resume_file_name, res_score, timestamp,
                no_of_pages, reco_field, cand_level, skills,
                recommended_skills, courses):

    DB_table_name = 'user_data'

    insert_sql = "INSERT INTO " + DB_table_name + """
        VALUES (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    rec_values = (
        name,
        email,
        contact,
        resume_file_name,
        str(res_score),
        timestamp,
        str(no_of_pages),
        reco_field,
        cand_level,
        skills,
        recommended_skills,
        courses
    )

    cursor.execute(insert_sql, rec_values)
    connection.commit()





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




    # Create table
    DB_table_name = 'user_data'
    table_sql = """
    CREATE TABLE IF NOT EXISTS user_data(
        ID INT NOT NULL AUTO_INCREMENT,
        Name VARCHAR(500) NOT NULL,
        Email_ID VARCHAR(500) NOT NULL,
        Contact_Number VARCHAR(20),
        Resume_File_Name VARCHAR(300),
        resume_score VARCHAR(8) NOT NULL,
        Timestamp VARCHAR(50) NOT NULL,
        Page_no VARCHAR(5) NOT NULL,
        Predicted_Field TEXT NOT NULL,
        User_level TEXT NOT NULL,
        Actual_skills TEXT NOT NULL,
        Recommended_skills TEXT NOT NULL,
        Recommended_courses TEXT NOT NULL,
        PRIMARY KEY (ID)
    );
    """
    cursor.execute(table_sql)
    if choice == 'User':
        st.markdown('<h6 style="text-align: left; color: white; background: linear-gradient(90deg, #4F46E5 0%, #00C2FF 50%, #4F46E5 100%); padding: 8px 12px; border-radius: 6px; font-family: \'Poppins\', sans-serif; font-weight: 600; margin: 8px 0; border: 1px solid rgba(255,255,255,0.3); box-shadow: 0 0 8px rgba(79, 70, 229, 0.4); text-shadow: 0 0 4px rgba(0, 194, 255, 0.3); font-size: 1em;">🧞‍♂️ Let the Genie Reveal Hidden Career Opportunities — Upload Your Resume Now!💨</h6>', unsafe_allow_html=True)
        
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is None and "resume_path" in st.session_state:
            del st.session_state["resume_path"]
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(1)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            resume_file_name = pdf_file.name

            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            # Step 1: Extract raw text
            text = extract_text_from_pdf(uploaded_file)
            
            # Step 2: Basic details
            name, email, phone = extract_basic_details(text)
            
            # Step 3: Skills based on your keyword list
            skill_keywords = ["python","java","html","css","react","node","sql","machine learning","data analysis"]
            skills = extract_skills(text, skill_keywords)

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
                # --- Skill-based Recommendation Logic ---
                                # --- Skill-based Recommendation Logic ---
                ds_keyword = [
                    'machine learning', 'deep learning', 'ml', 'dl',
                    'artificial intelligence', 'ai',
                    'tensorflow', 'keras', 'pytorch', 'scikit', 'sklearn',
                    'data analysis', 'data analytics',
                    'statistics', 'data science',
                    'nlp', 'computer vision',
                    'streamlit', 'flask',  
                    'numpy', 'pandas', 'matplotlib', 'seaborn'
                ]

                web_keyword = [
                    'react', 'react js', 'reactjs',
                    'javascript', 'js', 'typescript',
                    'html', 'css', 'bootstrap', 'tailwind',
                    
                    'node js', 'node.js', 'nodejs',
                    'express', 'express js', 'expressjs',
                    
                    'django', 'flask',
                    'php', 'laravel', 'wordpress', 'magento',
                    
                    'frontend', 'backend', 'full stack', 'fullstack',
                    
                    'api', 'rest api', 'restful', 'jwt',
                    'mysql', 'postgresql', 'sql', 
                    
                    'vite', 'webpack'
                ]

                android_keyword = [
                    'android', 'android development',
                    'kotlin', 'java', 'xml',
                    'flutter', 'dart',
                    'kivy', 'sdk'
                ]

                ios_keyword = [
                    'ios', 'swift', 'swiftui',
                    'objective-c',
                    'xcode', 'cocoa', 'cocoa touch',
                    'storekit', 'uikit'
                ]

                uiux_keyword = [
                    'ui', 'ux', 'ui/ux',
                    'figma', 'adobe xd', 'photoshop', 'illustrator',
                    'wireframe', 'prototype', 'mockup',
                    'user research', 'design system',
                ]

                st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🔧 Your Current Skills</h3>', unsafe_allow_html=True)
                # Get extracted skills (may be noisy)
                raw_skills = resume_data.get('skills') or []
                skills_list = []
                
                # Filter raw skills using our keyword lists
                all_keywords = ds_keyword + web_keyword + android_keyword + ios_keyword + uiux_keyword
                
                for skill in raw_skills:
                    s = skill.lower()
                    if any(kw in s for kw in all_keywords):
                        skills_list.append(skill)
                
                # If nothing matched, fallback to raw
                if not skills_list:
                    skills_list = raw_skills
                
                # Show cleaned skills
                st.markdown("### 🧠 Extracted Skills:")
                st.write(", ".join(skills_list))
                keywords = skills_list

                reco_field = ''
                rec_course = ''
                
                # 1. Initialize scores for each field
                scores = {'Data Science': 0, 'Web Development': 0, 'Android Development': 0, 'IOS Development': 0, 'UI-UX Development': 0}
                
                # 2. Loop through ALL skills and update scores
                # SAFER SKILLS LIST
                skills_list = resume_data.get('skills') or []
                
                # 2. Loop through ALL skills and update scores using substring match
                for skill in skills_list:
                    skill_lower = skill.lower()
                
                    if any(kw in skill_lower for kw in ds_keyword):
                        scores['Data Science'] += 1
                
                    if any(kw in skill_lower for kw in web_keyword):
                        scores['Web Development'] += 1
                
                    if any(kw in skill_lower for kw in android_keyword):
                        scores['Android Development'] += 1
                
                    if any(kw in skill_lower for kw in ios_keyword):
                        scores['IOS Development'] += 1
                
                    if any(kw in skill_lower for kw in uiux_keyword):
                        scores['UI-UX Development'] += 1
                
                
                # 3. Find the field with the highest score
                # Check if there are any matches at all
                if max(scores.values()) > 0:
                    reco_field = ""
                    recommended_skills = []
                    rec_course = []

                    reco_field = max(scores, key=scores.get)
                
                    # 4. Display the recommendation for the winning field
                    st.markdown(f'<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 12px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 18px; font-weight: 600; text-align: center; margin-top: 20px;">🔍 Our analysis says you are looking for <span style="color: #FFE066;">{reco_field}</span> Jobs!</div>', unsafe_allow_html=True)
                
                    if reco_field == 'Data Science':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">✨ Recommended Skills For You</h3>', unsafe_allow_html=True) 
                        recommended_skills = [
                            'Python', 'NumPy', 'Pandas',
                            'Matplotlib', 'Seaborn',
                            'Scikit-Learn', 'TensorFlow', 'Keras', 'PyTorch',
                            'Machine Learning Algorithms',
                            'Deep Learning Basics',
                            'Data Cleaning', 'Feature Engineering',
                            'Model Evaluation',
                            'NLP Basics', 'Computer Vision Basics',
                            'SQL for Data Analysis'
                        ]
                        st.markdown("### 🎯 Recommended Skills (Data Science):")
                        recommended_keywords = st.multiselect(
                            "Select recommended skills for Data Science:",
                            options=recommended_skills,
                            default=recommended_skills,
                            key="ds_reco"
                        )
                        
                        rec_course = course_recommender(ds_course)

                
                    elif reco_field == 'Web Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True) 
                        recommended_skills = [
                            'HTML5', 'CSS3', 'JavaScript', 'TypeScript',
                            'React', 'React Hooks', 'Redux',
                            'Node.js', 'Express.js',
                            'REST APIs', 'JWT Authentication',
                            'MongoDB', 'Mongoose',
                            'MySQL', 'PostgreSQL',
                            'Git', 'GitHub', 
                            'Responsive Design', 'Tailwind CSS', 'Bootstrap',
                            'Docker (Basics)', 'CI/CD (Basics)'
                        ]
                        st.markdown("### 🎯 Recommended Skills (Web Development):")
                        recommended_keywords = st.multiselect(
                            "Select recommended skills for Web Development:",
                            options=recommended_skills,
                            default=recommended_skills,
                            key="web_reco"
                        )
                        
                        rec_course = course_recommender(web_course)

                
                    elif reco_field == 'Android Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True)
                        recommended_skills = [
                            'Kotlin', 'Java', 'Android Studio',
                            'XML Layouts', 'Jetpack Components',
                            'Firebase', 'Room Database',
                            'Retrofit', 'REST API Integration',
                            'MVVM Architecture',
                            'Material Design'
                        ]
                        st.markdown("### 🎯 Recommended Skills (Android Development):")
                        recommended_keywords = st.multiselect(
                            "Select recommended skills for Android:",
                            options=recommended_skills,
                            default=recommended_skills,
                            key="android_reco"
                        )
                        
                        rec_course = course_recommender(android_course)
                        
                
                    elif reco_field == 'IOS Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True)
                        recommended_skills = [
                            'Swift', 'SwiftUI',
                            'Xcode', 'UIKit',
                            'Cocoa Touch',
                            'CoreData',
                            'REST API Integration',
                            'Auto-Layout',
                            'MVVM Architecture'
                        ]
                        st.markdown("### 🎯 Recommended Skills (iOS Development):")
                        recommended_keywords = st.multiselect(
                            "Select recommended skills for iOS:",
                            options=recommended_skills,
                            default=recommended_skills,
                            key="ios_reco"
                        )
                        
                        rec_course = course_recommender(ios_course)

                
                    elif reco_field == 'UI-UX Development':
                        st.markdown('<h3 style="text-align: left; color: #00C2FF; font-family: Poppins, sans-serif; font-weight: 600; margin-top: 30px;">🚀 Recommended Skills for You</h3>', unsafe_allow_html=True)
                        recommended_skills = [
                            'Figma', 'Adobe XD',
                            'Wireframing', 'Prototyping',
                            'User Flow Design',
                            'Design Systems',
                            'User Research',
                            'Typography', 'Color Theory',
                            'UI Design', 'UX Writing'
                        ]
                        st.markdown("### 🎯 Recommended Skills (UI/UX Design):")
                        recommended_keywords = st.multiselect(
                            "Select recommended skills for UI/UX:",
                            options=recommended_skills,
                            default=recommended_skills,
                            key="uiux_reco"
                        )
                        
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
                
                # Creating a list of checks to perform. Each item is a tuple containing:
                # (keywords_to_check, section_name, success_message, failure_message)
                checks = [
                    (['Objective'], 'Objective', '[+] Awesome! You have added your Career Objective', '[-] Please add your career objective...'),
                    (['Declaration'], 'Declaration', '[+] Awesome! You have added the Declaration', '[-] Please add a Declaration at the end...'),
                    (['Hobbies', 'Interests'], 'Hobbies/Interests', '[+] Awesome! You have added your Hobbies', '[-] Consider adding a Hobbies section...'),
                    (['Achievements'], 'Achievements', '[+] Awesome! You have added your Achievements', '[-] Please add any Achievements...'),
                    (['Projects'], 'Projects', '[+] Awesome! You have added your Projects', '[-] Please add any Projects you have worked on...')
                ]
                
                for keywords, section_name, success_msg, failure_msg in checks:
                    if any(keyword in resume_text for keyword in keywords):
                        resume_score += 20
                        st.markdown(
                            f"""
                            <p style="font-size:23px; color:#00FF88; font-family:Poppins; margin:5px 0;">
                                ✔ <b>{success_msg}</b>
                            </p>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <p style="font-size:23px; color:#FF5555; font-family:Poppins; margin:5px 0;">
                                ❌ <b>{failure_msg}</b>
                            </p>
                            """,
                            unsafe_allow_html=True
                        )




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
                    time.sleep(0.01)  # Make it a bit faster
                    my_bar.progress(i + 1)
                
                # We already have the score in the 'resume_score' variable
                # st.markdown(f'<div>📝 ?Your Resume Writing Score: <span>{resume_score}</span></div>', unsafe_allow_html=True)                # st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.markdown(f'<div style="background: linear-gradient(90deg, #4F46E5, #00C2FF); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 20px; font-weight: 600; text-align: left; margin-top: 20px;">📝 Your Resume Writing Score: <span style="color: #FFE066;">{resume_score}</span></div>', unsafe_allow_html=True)
                st.markdown('<div style="background: linear-gradient(90deg, #FFA500, #FF6347); color: white; padding: 10px; border-radius: 10px; font-family: \'Poppins\', sans-serif; font-size: 16px; font-weight: 600; text-align: left; margin-top: 10px;">ℹ️ Note: This score is calculated based on the content that you have in your Resume.</div>', unsafe_allow_html=True)
                st.balloons()

                contact = resume_data.get('mobile_number', 'Not Found')
                file_name = pdf_file.name
                
                insert_data(
                    name,                     
                    email,                    
                    phone,                    
                    resume_file_name,         
                    str(resume_score),        
                    timestamp,                
                    str(no_of_pages),         
                    reco_field,               
                    cand_level,               
                    skills,                   
                    recommended_skills,       
                    rec_course                
                )
                                
                
                # Display a random resume video
                display_random_video(resume_videos, "🎥 Bonus Video for Resume Writing Tips💡")
               
                # Display a random interview video
                display_random_video(interview_videos, "🎥 Bonus Video for Interview Tips💡")
               
                connection.commit()

            
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.markdown('<h6 style="text-align: left; color: white; background: linear-gradient(90deg, #4F46E5, #00C2FF); padding: 10px 12px; border-radius: 8px; font-family: \'Poppins\', sans-serif; font-weight: 600; margin: 8px 0; border: none; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); font-size: 1em;">✨ Welcome to Admin Dashboard</h6>', unsafe_allow_html=True)
        
        # ------------------------------
        # ADMIN LOGIN USING SESSION STATE
        # ------------------------------
        if "admin_logged_in" not in st.session_state:
            st.session_state["admin_logged_in"] = False
        
        # SHOW LOGIN FORM ONLY IF NOT LOGGED IN
        if not st.session_state["admin_logged_in"]:
        
            ad_user = st.text_input("Username")
            ad_password = st.text_input("Password", type='password')
        
            if st.button("Login"):
                if ad_user == st.secrets["admin"]["user"] and ad_password == st.secrets["admin"]["password"]:
                    st.session_state["admin_logged_in"] = True
                    st.success("Welcome Admin!")
                else:
                    st.error("Wrong ID & Password! Please try again.")
        
        # IF LOGGED IN → SHOW DASHBOARD
        if st.session_state["admin_logged_in"]:
        
            # --- Simplified Data Fetching ---
            cursor.execute("SELECT * FROM user_data")
            data = cursor.fetchall()
        
            column_names = [
                'ID', 'Name', 'Email', 'Contact_Number', 'Resume_File_Name',
                'Resume Score', 'Timestamp', 'Total Page', 'Predicted Field',
                'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course'
            ]
        
            df = pd.DataFrame(data, columns=column_names)
        
            st.dataframe(df)
        
            # --- Search & Filters ---
            st.markdown("### 🔍 Search & Filters")
            search_text = st.text_input("Search by Name, Email or File Name:")
        
            if search_text:
                df = df[df.apply(lambda row: row.astype(str).str.contains(search_text, case=False).any(), axis=1)]
        
            fields = df["Predicted Field"].unique()
            selected_field = st.selectbox("Filter by Predicted Field:", ["All"] + list(fields))
            if selected_field != "All":
                df = df[df["Predicted Field"] == selected_field]
        
            levels = df["User Level"].unique()
            selected_level = st.selectbox("Filter by Experience Level:", ["All"] + list(levels))
            if selected_level != "All":
                df = df[df["User Level"] == selected_level]
        
            score_filter = st.selectbox("Filter by Resume Score:", ["All", "> 40", "> 60", "> 80"])
            if score_filter == "> 40":
                df = df[df["Resume Score"].astype(int) > 40]
            elif score_filter == "> 60":
                df = df[df["Resume Score"].astype(int) > 60]
            elif score_filter == "> 80":
                df = df[df["Resume Score"].astype(int) > 80]
        
            sort_option = st.selectbox(
                "Sort by:",
                ["None", "Name (A-Z)", "Score High → Low", "Score Low → High", "Newest First", "Oldest First"]
            )
            if sort_option == "Name (A-Z)":
                df = df.sort_values(by="Name")
            elif sort_option == "Score High → Low":
                df = df.sort_values(by="Resume Score", ascending=False)
            elif sort_option == "Score Low → High":
                df = df.sort_values(by="Resume Score", ascending=True)
            elif sort_option == "Newest First":
                df = df.sort_values(by="Timestamp", ascending=False)
            elif sort_option == "Oldest First":
                df = df.sort_values(by="Timestamp", ascending=True)
        
            st.markdown("### 📋 Filtered Results:")
            st.dataframe(df)
            st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
        
            # ------------------------------
            # 4.6 Dynamic Charts (Filtered DF)
            # ------------------------------
            st.subheader("📊 Predicted Field Distribution (Filtered)")
            if len(df) > 0:
                field_counts = df['Predicted Field'].value_counts()
                fig1 = px.pie(values=field_counts.values, names=field_counts.index, title='Predicted Field (Filtered)')
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No data available for chart.")
        
            st.subheader("📊 User Experience Level (Filtered)")
            if len(df) > 0:
                level_counts = df['User Level'].value_counts()
                fig2 = px.pie(values=level_counts.values, names=level_counts.index, title='User Experience Level (Filtered)')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data available for chart.")
        
    
run()