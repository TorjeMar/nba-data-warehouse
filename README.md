IKT553: Intelligent Database Management 
Instructor:  Vladimir Zadorozhny (http://www.pitt.edu/~viz/) 
e-mail: viz@pitt.edu 

## PROJECT: Data Warehousing Strategies 

The project is done in groups and is documented by a written group report. A demo will be scheduled for 
each group.  The groups are ``self-policed''. Each group will work on a different data-intensive application 
as explained below. 

## Project Description 
You are to design, implement, demonstrate, and document a Data Warehouse that consolidates data 
and  supports efficient data-driven decision making for a specific application domain. Each group will 
have to choose  a different   application (e.g., e-commerce, health management, epidemiological data 
monitoring, etc., see the sample data sets at the end of this descripttion), prepare your application
specific list of decision support queries and discuss them with instructor. You will need to select data 
sources to load your Data Warehouse, which may include both real and simmulated data.  In the process 
of the data loading you may need to perform  information transformation if needed. 


First, you should implement a relational Data Warehouse, that includes designing proper 
multidimensional model and implementing it in a star schema. After implementing a relational Data 
Warehouse you should provide an alternative implementations of the Data Warehouse backend using two 
NoSQL database systems. I suggest you to use Neo4j and MongoDB, but your group may choose other 
systems. 

While project groups are self-policied and each group member should be involved in each project task, I 
suggest you to select a group coordinator and assign group member(s) with primary responsibility for 
each of the following topics: 

1. Relational Data Warehouse design and implementation (this would include implementing a front 
end a relational backend); 
2. Using NoSQL database system 1 to provide an aternative implementation of the Data Warehouse 
system; 
3. Using NoSQL database system 2 to provide an aternative implementation of the Data Warehouse 
system. 
4. Dockerize your project implementation using containers for RDBMS, NoSQL database system, 
and Kafka with streaming your project data a la DELab7. 
5. (Optional for extra credit) Apply kSQL at any stage of your data processing and describe your 
experience in the project report (use DELab8 and DELab9 for insights). 

**Assumptions:** It is acceptable to make assumptions about the application provided that: 1) they are 
explicitly stated in the final report, 2) they are "reasonable". If you have a question about the acceptability 
of any of your assumptions, check with the instructor. 

**Report:** A  final report should be handed in for grading at the end of the term. The report must be 
formatted in a reasonable manner.  

The final report must contain:  
1. [ ] A short overview of the system including identification of the various types of users, administrators, etc. who will be accessing the system in various ways.   
2. [ ] A list of assumptions that you have made about the system.  
3. [ ] A description of the data that will be maintained in your system.   
4. [ ] A description of the data loading process including required data cleaning and data transformation.   
5. [ ] A description of STAR schema design. Specification of FACT table and tables for the Data Warehouse dimensions (including corresponding DDL statements). The SQL statements to load the STAR schema.  
6. [ ] Specification of pre-aggregated summary tables (including corresponding DDL statements). The SQL 
statements for creation and populating of the summary tables. Specification of of batch job to load 
data in pre-aggregated summaries.  
7. [ ] A description of Data Warehouse queries and front-ends required for the warehouse.  
8. [ ] Some example scenarios of how various types of users will interact with the system.  
9. [ ] A description of alternative implementation of your DW system using two NoSQL platforms. 
10. [ ] A decription of dockerization of your project. 
11. [ ] A description of your data streaming functionality. 
12. [ ] A detailed comparison of relational and NoSQL implementations with explanation of advantages and 
disadvantages of each approach 
In addition, a demo of the working system will be required. All members of the group must attend this 
demo, and must be prepared to explain and demonstrate those aspects of the project for which they were 
responsible. The source code for the project should be available on-line during the demonstration.

**Some specific questions and answers:**

1. For the front-end solution, are we thinking correctly if there should be four 'sites', one where 
you choose the type of database, and three additional for each database type? More precise, 
should there be an individual UI for MySQL, Neo4j, and MongoDB? 
Answer:  I expect you to have an “umbrella” front-end from which you should access all your 
alternative DW implementations. 
2. Report requirement 6: "Specification of pre-aggregated summary tables (including 
corresponding DDL statements). The SQL statements for the creation and populating of the 
summary tables. Specification of nightly scheduled batch job to summarize data." Should this 
batch contain only new data, all data, or changed data?  
Answer: This should not include any data, just SQL specifications. 
3. Is the pre-aggregated summary tables the same as the nightly scheduled batch? If not, what is 
the main difference? 
Answer: Nightly batch job includes loading Fact and dimension tables from your operational 
databases. Your pre-aggregated summary tables should be created and populated from the 
Fact and dimension tables. Population of the pre-aggregated tables should be specified as a 
separate batch job. 
4. Report requirement  9 states that we should provide a description of our DW system for two 
NoSQL platforms. Which of the previous requirements (e.g., STAR schema, summary tables, 
example scenarios) do you think also should be a part of the description of these two 
platforms? 
Answer: Your implementation should include some analogy of star schema and summary 
tables, but since your alternative implementations are not relational, those concepts should be 
represented using data model of your NoSQL platforms (e.g., documents for MongoDB or 
graphs for Neo4j).  This is one of the major project objectives: to explore how the relational 
DW concepts can  be mapped into NoSQL systems. 
.Here are some suggested data sets for your project implementation, feel free to choose other data sets.  
Climate datasets: 
http://www.ncdc.noaa.gov/cdo-web/- interactive online search and download for up to date climate data. 
The problem is that they have very small limit for one time download (5000 stations at a time). 
Project Tycho: 
https://www.tycho.pitt.edu/ 
Genomic Data Commons: 
https://gdc.cancer.gov/ 
Global Terrorism Database 
https://www.start.umd.edu/gtd/ 