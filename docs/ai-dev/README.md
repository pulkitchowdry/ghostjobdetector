## AI Tools 

|   Tool    |  Usage                                                                |
| --------  | --------------------------------------------------------------------- |
| ChatGPT   |   1. Brainstorming the idea and features (Research)           <br>    |
|           |   2. Debugging issues and understanding error messages         <br>   |
|           |   3. Implementation of better Natural Language Processing features <br>|
|           |   4. Assistance in deploying on Vercel and AWS Lambda <br>            |
| v0        |   1. Creation of the initial boilertemplate  <br>                     |
|           |   2. Frontend design                      <br>                        |
| Claude    |   1. FastAPI based backend development     <br>                       |
|           |   2. API design and database schema development<br>                   |


## Development Approach with AI 

### Brainstorming
Initially the idea was brainstormed with ChatGPT which helped in researching the methods in which ghost jobs can be identified. It was also helpful in suggesting various natural language processing methods to evaluate job description which is one of the main criteria.

### Plan
Once the idea and the required features were decided, ChatGPT was used in planning the tech stack, architecture and the overall design of the application along with the need to have an extension. I also used AI in planning our different ATS systems work and how the application can be integrated with them.

### Initial implementation
A carefully crafted prompt was designed and given to v0 to create the initial boilertemplate of the application. The prompt contained the below details,
1. Goal of the application
2. List of features necessary in the initial prototype
3. Design of the frontend and the Chrome extension
4. Tech stack for the backend
5. API structure

### Improving the prototype
Claude and ChatGPT were later used together in improving specific features which were either missing or not implemented properly in the initial prototype. The prompts were specific with exact parts that need to be implemented.

Database schema was also prepared using AI to help in implementing a cached feature so that ATS systems do not block the application.

### Fixing issues
Multiple issues were observed like possible blocking of the application by ATS, issues in deploying the backend on AWS Lambda and proper integration with ATS tools like smartrecruiters.

The decisions on how to solve them were taken by me after proper brainstorming with AI tools on what are the possible solutions. Initially the backend was deployed on ngrok but the backend was not available always as it was dependent on the hardward device to be On always. So later a free alternate AWS Lambda was found and the backend was deployed using the serverless framework.

## Reflection 

### What worked?
AI tools mentioned above were great in brainstorming ideas, features, implementing a good initial prototype which drastically reduced the development time. 
They were also good in identifying the root cause of different errors and assisted in debugging.

### What failed?
AI tools were not very good in identifying problems listed below,
1. ATS systems blocking due to multiple requests from the same IP address.
2. API structure for each ATS system is different and so to have one generic request-response template for all of them does not work.
3. Suggested Railway as a deployment option when AWS Lambda and ngrok were free alternatives.

### Changes made and the rationale
After identifying each of the problems above, the prompts to the AI tools were modified by me where I first brainstormed the possible solutions, identified each one's advantages and disadvantages and then implemented the best solution for my requirement.


1. ATS systems blocking issue
On further brainstorming this problem with Claude, I identified that a better solution is to cache the results in a database and use them instead of hitting the ATS API endpoints constantly for each request. This meant that the job list in the database is not latest but it solved the main problem of not getting blocked by the ATS systems.

2. API design of each ATS system
When I came to know that the requests were failing for different API systems, I decided on implementing the system for 2 ATS systems first and delayed the implementation for other systems later as the main requirement is to have the MVP ready so that the feature works.

3. Deployment issues
With regards to deployment, I knew that Railway was not the ideal option and so looked for various other alternatives online as AI tool kept suggesting Railyway, Render, etc. which had a free plan but were not ideal for my requirements. AWS Lambda offered a free tier that required more technical expertise than the other tools but was the most ideal solution for me.

