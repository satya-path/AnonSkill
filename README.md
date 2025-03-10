# AnonSkill

# AnonSkill


ZerePy-CLI (JobAgent) > agent-action openai parse-input "show me top jobs 
 in Delhi"
Performing action: parse-input on connection: openai
HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Result: {'action': 'find_jobs', 'parameters': {'search_query': 'top job opportunities in Delhi', 'location': 'Delhi', 'job_type': None}}
--------------------------------------------------------------------      

ZerePy-CLI (JobAgent) > agent-action openai find-jobs {'search_query': 't 
op jobs in Delhi', 'location': 'Delhi', 'job_type': None}
Performing action: find-jobs on connection: openai
HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Result: Here are 5 current job listings in Delhi:

1. **Job ID:** JD001
   **Company Name:** Tata Consultancy Services
   **Job Title:** Software Developer
   **Location:** Delhi
   **Brief Description:** Seeking a talented software developer with expertise in Java and cloud technologies. Responsible for designing, developing, and maintaining applications while collaborating with cross-functional teams.

2. **Job ID:** JD002
   **Company Name:** HCL Technologies
   **Job Title:** Business Analyst
   **Location:** Delhi
   **Brief Description:** HCL is looking for a Business Analyst to analyze business needs and document requirements. Must possess strong analytical skills and experience with project management methodologies.

3. **Job ID:** JD003
   **Company Name:** Infosys Limited
   **Job Title:** Data Scientist
   **Location:** Delhi
   **Brief Description:** Join Infosys as a Data Scientist, focusing on statistical analysis and machine learning. Ideal candidates should have a background in data analytics and programming skills (Python/R).

4. **Job ID:** JD004
   **Company Name:** Accenture
   **Job Title:** Digital Marketing Specialist
   **Location:** Delhi
   **Brief Description:** Accenture is hiring a Digital Marketing Specialist to create and manage digital campaigns. Candidates should have experience in SEO, PPC, and social media marketing.

5. **Job ID:** JD005
   **Company Name:** Wipro
   **Job Title:** Cyber Security Analyst
   **Location:** Delhi
   **Brief Description:** Wipro seeks a Cyber Security Analyst responsible for protecting IT infrastructure. Applicants should have experience in risk assessments and familiarity with security frameworks.

Feel free to reach out if you need more information on any of these positions!
--------------------------------------------------------------------      

ZerePy-CLI (JobAgent) > agent-action openai parse-input "Show details of: 
 **Job ID:** JD004
   **Company Name:** HealthFirst Technologies
   **Job Title:** UX/UI Designer
   **Location:** New Delhi
   **Description:** Looking for a creative UX/UI designer to enhance user 
 experience for our web and mobile applications, ensuring a user-friendly 
 navigation."
Performing action: parse-input on connection: openai
HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Result: {'action': 'view_job', 'parameters': {'description': 'UX/UI Designer', 'company': 'HealthFirst Technologies', 'job_location': 'New Delhi'}} 
--------------------------------------------------------------------

ZerePy-CLI (JobAgent) > agent-action openai apply-to-job {'description':  
'UX/UI Designer', 'company': 'HealthFirst Technologies', 'job_location':  
'New Delhi'}
Performing action: apply-to-job on connection: openai
HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Result: To assist you better, I'll need the specific company or job posting details for the UX/UI Designer position you're interested in. Please provide that information, and I can then give you the appropriate application process and link.
--------------------------------------------------------------------  

ZerePy-CLI (JobAgent) > exit

Goodbye! 👋
