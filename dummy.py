dummy_prompt = """You are Employee Experience Manager at an unnamed nonprofit company, of about 100 to 5,000 employees. This company is a hybrid work environment. This company really cares about the employee experience throughout the entire employee lifecycle from onboarding to health and wellness programs and CSR initiatives to offboarding and more. The tone should be friendly, supportive, and encouraging and not be too serious. Always refer to the HR Team as the People Team instead.
You need to create a few different pieces of short text to be placed on a LinkedIn banner by a graphic designer. Employees will use the LinkedIn banners on their LinkedIn profiles to help act as advocates for company initiatives. Your job is to brainstorm a theme for the backgrounds and create some draft text.

Always use the outlined character count ranges, # of questions or topics and answers, and everything else outlined in the Layout Descriptions. Never deviate from the Layout Description, and only create content for the fields it specifies.

The LinkedIn Cover topic is announcing we're hiring software developers and want great talent. Come up with 25 variations. Never output in code.

For each variation include:

- A title of 3 lines, every line is maximum 10 characters each
- A subtitle of 8-13 characters
- A hashtag of between 15-20 characters
- An illustration suggestion that includes the prompt “The illustration should be in a modern, flat style with smooth lines and vibrant colors. The background should be simple and clean, without any distracting elements, to keep the focus on the main element”

Use this structure for the response:
Variation 1 -
Title:
Subtitle:
Hashtag:
Illustration:"""

dummy_json = {"Launch Employee Referral Program":[{"name":"Step 1: Launch Referral Program","description":"Create awareness of the referral program and getting employees excited about participating.","elements":[{"title":"Referral Program Manager Guide","description":"A comprehensive guide for managers to help them promote the referral program and support their teams in participating.","content_type":"Manager One-Pager","type":"Design"},{"title":"Identify Stakeholders","description":"ensure managers, HR, and employees understand their role in launching and promoting the program successfully.","content_type":"Identify Stakeholders","type":"Educational Element"},{"title":"Referral Program Policy","description":"N/A","content_type":"Policy","type":"Document"},{"title":"Referral Program FAQ","description":"A document addressing common questions about the referral program, providing clarity and encouraging participation.","content_type":"FAQ","type":"Design"},{"title":"Share Open Jobs Request","description":"Ask Employees for Referrals","content_type":"Communication","type":"Communication"},{"title":"Referral Program Form","description":"N/A","content_type":"Form","type":"Document"},{"title":"Referral Program Logo","description":"A unique, memorable logo representing the referral program, used across all marketing and communication materials.","content_type":"Logo Landscape","type":"Design"},{"title":"Top Tip","description":"Provide guidance on where to direct questions and how to prioritize high-quality referrals.","content_type":"Top Tip","type":"Educational Element"},{"title":"Referral Program Contest","description":"Introduce Referral Program/Contest","content_type":"Communication","type":"Communication"}]},{"name":"Step 2: Promote Employee Participation","description":"Encourage employees to actively participate in the referral program by offering attractive incentives.","elements":[{"title":"We're Hiring Social Post","description":"Ask Employees to Share Open Jobs ","content_type":"Social Post","type":"Communication"},{"title":"Referral Program Poster","description":"Eye-catching posters placed around the office to raise awareness and encourage employees to refer candidates.","content_type":"Poster","type":"Design"},{"title":"Referral Program Zoom Backgrounds","description":"Branded virtual backgrounds to promote the referral program during online meetings and encourage participation.","content_type":"Zoom Background","type":"Design"},{"title":"Referral Program Gift Cards","description":"Incentives in the form of gift cards provided to employees as a reward for successful referrals.","content_type":"Gift Card","type":"Design"},{"title":"We're Hiring LinkedIn Cover","description":"A visually appealing banner designed for LinkedIn profiles to announce job openings and attract potential candidates, showcasing the company as a great place to work.","content_type":"LinkedIn Cover","type":"Design"},{"title":"Define Goal","description":"Set clear expectations regarding the specific skills, experiences, or job roles needed for referrals and what success entails. This will clarify the ideal candidate profiles for employees and provide clear guidance on whom to refer.","content_type":"Define Goal","type":"Educational Element"},{"title":"Referral Program TV Display","description":"Dynamic digital signage displayed on office TVs, highlighting referral success stories and program details.","content_type":"TV Display","type":"Design"}]},{"name":"Step 3: Encourage Ongoing Engagement","description":"Once the program is live, it’s crucial to maintain momentum. Consistent reminders, updates, and recognition through shout-outs keep the program top of mind, ensuring employees continue to refer candidates.","elements":[{"title":"Referral Program Infographic","description":"Craft compelling infographics to simplify data","content_type":"Infographic","type":"Design"},{"title":"Top Tip","description":"Encourage managers to regularly remind their teams about the referral program during meetings or on internal platforms.\n","content_type":"Top Tip","type":"Educational Element"},{"title":"Analyze Data","description":"Help managers and program administrators analyze the progress of the referral program by tracking the number of referrals, successful hires, and participation rates over time.","content_type":"Analyze Data","type":"Educational Element"},{"title":"Referral Program Survey","description":"Survey/Feedback for Referral Program","content_type":"Communication","type":"Communication"},{"title":"Employee Referral Ask ","description":"Provide Social Post Graphics to Share with Employees' Networks","content_type":"Communication","type":"Communication"},{"title":"Referral Contest Reminder","description":"Remind Employees About Referral Program","content_type":"Communication","type":"Communication"},{"title":"Referral Program Manager Reinforcement","description":"Ask Manager to Remind Direct Reports About Referral Program","content_type":"Communication","type":"Communication"}]},{"name":"Step 4: Recognize and Reward","description":"Recognizing top referrers through leaderboards and providing public recognition to reward participation.","elements":[{"title":"Thank You For Your Referrals","description":"Thank Employees for Submitting Referrals","content_type":"Communication","type":"Communication"},{"title":"Quick Win","description":"Offer a quick and easy way for managers to publicly acknowledge and thank employees who participate, such as sending a personalized message or shout-out via internal communication channels.","content_type":"Quick Win","type":"Educational Element"},{"title":"Referral Program Swag","description":"Fun and branded items (like t-shirts or mugs) given to employees to incentivize and reward successful referrals.","content_type":"Swag","type":"Design"},{"title":"Referral Program Leaderboard","description":"A digital or physical leaderboard showcasing top referrers, fostering healthy competition and motivating employees to participate.","content_type":"Recognition","type":"Design"},{"title":"Referral Program Certificate","description":"A formal certificate given to employees who successfully refer candidates, recognizing their contribution to the company.","content_type":"Certificate","type":"Design"},{"title":"Top Referrer Shout Out","description":"Reward/Recognize Top Referrer","content_type":"Appreciation","type":"Communication"}]}],"Enhance Employer Brand":[{"name":"Step 1: Launch Employer Branding Initiatives","description":"Introduce and implement key employer branding efforts across the organization","elements":[{"title":"Top Tip","description":"Provide managers and employees with a quick tip on how to share their professional experiences on social media in a way that aligns with the company's employer brand.","content_type":"Top Tip","type":"Educational Element"},{"title":"Do's and Don'ts of Social Media","description":"N/A","content_type":"FAQ","type":"Design"},{"title":"Employer Brand FAQ","description":"N/A","content_type":"FAQ","type":"Design"},{"title":"Employer Brand Guidelines","description":"Reminder of employer brand guidelines in all communications to maintain consistency and attract top talent.","content_type":"Communication","type":"Communication"},{"title":"Define Goal","description":"Clarify the objectives of the employer branding initiatives, such as strengthening the company's reputation, attracting top talent, and empowering employees to participate.","content_type":"Define Goal","type":"Educational Element"},{"title":"Manager's Guide to Employer Brand","description":"N/A","content_type":"Manager One-Pager","type":"Design"},{"title":"Employee Advocacy Program Kickoff","description":"Learn how you can help enhance our employer brand by participating in your employee advocacy program.","content_type":"Communication","type":"Communication"}]},{"name":"Step 2: Engage Employees and Promote Employer Brand","description":"Engaging employees to become brand ambassadors and encouraging them to share their positive experiences both internally and externally to build a stronger employer brand.","elements":[{"title":"Company Culture Showcase Social Post","description":"A social media post highlighting our unique company culture to attract top talent and showcase what makes us a great place to work.","content_type":"Social Post","type":"Communication"},{"title":"Identify Stakeholders","description":"Highlight key employees or managers who will act as primary advocates for the employer brand, sharing their experiences and promoting the brand on external platforms.","content_type":"Identify Stakeholders","type":"Educational Element"},{"title":"Encourage Employees to Engage on Social Media","description":"Motivate employees to participate in social media activities to boost the company's online presence and employer brand","content_type":"Communication","type":"Communication"},{"title":"Employee Success Spotlight Social Post ","description":"Highlight an outstanding employee, sharing their inspiring career journey and achievements at your company.","content_type":"Social Post","type":"Communication"},{"title":"Share Your Story!","description":"Invite employees to share their career success stories and experiences working with the company, to be featured in internal communications and on our social media channels.","content_type":"Communication","type":"Communication"},{"title":"Company Showcase","description":"N/A","content_type":"Poster","type":"Design"}]},{"name":"Step 3: Promote Brand Consistency and Community Involvement","description":"Maintain momentum and ensure brand consistency across all communications and encouraging employees to engage actively with the company's values, both online and in-person.","elements":[{"title":"Employee Newsletter","description":"Keep employees informed, engaged, and connected with company updates, areas of improvement, achievements, and other important info.","content_type":"Communication","type":"Communication"},{"title":"Analyze Data","description":"Track engagement with internal communications and social media posts highlighting employee success to gauge how well recognition efforts are resonating with employees and external audiences.","content_type":"Analyze Data","type":"Educational Element"},{"title":"Encourage Company Reviews","description":"Remind employees to provide feedback on review sites to enhance the employer brand and attract top talent.","content_type":"Communication","type":"Communication"},{"title":"Quick Win","description":"Offer simple tasks for employees to advocate for the brand, such as sharing upcoming events or positive work experiences online, which can quickly contribute to enhancing the brand.","content_type":"Quick Win","type":"Educational Element"},{"title":"Employee Spotlight","description":"Recognize an employee each month/quarter for achievements or personal milestones.","content_type":"Appreciation","type":"Communication"},{"title":"Share Brand Kit","description":"Update social media and communications using a brand kit to consistently reflect your employer brand.","content_type":"Communication","type":"Communication"},{"title":"Discover What Makes Us A Great Place to Work","description":"Highlight your workplace, company culture, and team dynamics to attract interviewing talent.","content_type":"Communication","type":"Communication"}]}]}
