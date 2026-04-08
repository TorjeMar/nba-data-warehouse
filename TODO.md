# Project TODO

This file tracks progress against the stated project requirements for the IKT453 data warehousing project.

Status key:
- `[x]` done
- `[-]` partially done / scaffolded
- `[ ]` not done

## Implementation Status

### Infrastructure And Setup

- [x] Dockerized database infrastructure for MySQL, MongoDB, and Neo4j
- [x] Local database admin dashboards via phpMyAdmin, mongo-express, and Neo4j Browser
- [x] Python SDK dependencies for MySQL, MongoDB, and Neo4j
- [x] Basic project structure for SQL assets, ETL code, docs, config, and tests

### Data Source And ETL

- [x] Source dataset identified and included locally as `data/box_scores.jsonl`
- [x] Source fields documented
- [x] Dataset download helper script
- [x] Shared ETL transformation layer for the basketball box score dataset
- [x] ETL loaders for MySQL, MongoDB, and Neo4j
- [x] Add correct handling for inorrect time entry (see warnings when loading entire dataset using mysql)
- [x] Source-to-warehouse enrichment for game date, season, matchup, and home/away metadata
- [ ] Scheduled batch jobs for recurring warehouse loads
- [ ] Streaming/Kafka-based data ingestion

### Relational Warehouse

- [x] MySQL star schema design
- [x] Fact table definition
- [x] Dimension table definitions
- [x] Pre-aggregated summary table definitions
- [x] MySQL schema initialization via Docker Compose (`/docker-entrypoint-initdb.d`)
- [x] Verified end-to-end load into a live MySQL container
- [ ] Relational analytical query set for the final report/demo

### NoSQL Alternatives

- [x] MongoDB alternative warehouse design
- [x] MongoDB collection validator and index definitions
- [x] MongoDB summary aggregation examples
- [x] Neo4j alternative warehouse design
- [x] Neo4j constraints and load shape
- [x] Neo4j analytical query examples
- [x] MongoDB schema/bootstrap initialization (collections, indexes, validators)
- [x] Neo4j schema/bootstrap initialization (constraints, indexes, seed data)
- [x] Verified end-to-end load into a live MongoDB container
- [x] Verified end-to-end load into a live Neo4j container
- [ ] Explicit comparison dataset/results across all three backends

### Documentation

- [x] Root project README updated to reflect current implementation
- [x] Architecture notes added
- [-] Description of the data loading and transformation process
- [-] Documentation of relational and NoSQL warehouse designs
- [ ] Final report draft
- [ ] Demo script / presentation flow

### Frontend And User Workflows

- [ ] Umbrella frontend for accessing all warehouse implementations
- [ ] Description of user types
- [ ] Example user scenarios and workflows
- [ ] Description of warehouse queries and frontend views

## Requirement Checklist

This section maps the course requirements to current status.

1. A short overview of the system including various user types
- [-] System overview exists in the README and architecture docs
- [ ] User types and access patterns are not defined yet

2. A list of assumptions made about the system
- [ ] Not documented as a dedicated assumptions list yet

3. A description of the data maintained in the system
- [-] Dataset and source fields are documented
- [ ] Final warehouse data description still needs to be written formally

4. A description of the data loading process including cleaning and transformation
- [-] ETL code exists and basic behavior is documented
- [ ] Formal report-style explanation of cleaning/transformation steps is still needed

5. A description of the STAR schema design including fact/dimensions, DDL, and SQL load statements
- [-] Star schema DDL exists
- [ ] SQL load statement documentation for the final report is still incomplete
- [ ] Live validation in MySQL is still pending

6. Pre-aggregated summary tables, DDL, SQL population statements, and batch jobs
- [-] Summary table DDL exists
- [ ] SQL population scripts are not implemented yet
- [ ] Batch job specification is not implemented yet

7. A description of warehouse queries and frontends required for the warehouse
- [-] Some analytical queries exist for Neo4j and MongoDB summaries
- [ ] Full cross-backend query set is not defined yet
- [ ] Frontend requirements and implementation are not done

8. Example scenarios for how users interact with the system
- [ ] Not done

9. A description of alternative implementation using two NoSQL platforms
- [-] MongoDB and Neo4j designs are implemented in scaffold form
- [ ] Final written comparison/description is not finished
- [ ] Live validation for both NoSQL backends is still pending

10. A description of dockerization of the project
- [-] Docker setup exists and is documented operationally
- [ ] Final report description of dockerization is still not written

11. A description of data streaming functionality
- [ ] Not done

12. A detailed comparison of relational and NoSQL implementations with pros and cons
- [ ] Not done

## Suggested Next Steps

Recommended next implementation tasks:

1. Run and validate the ETL loaders against live MySQL, MongoDB, and Neo4j containers.
2. Add schema/bootstrap runner scripts so setup is reproducible.
3. Implement summary-table population logic for MySQL and materialized aggregate loading across backends.
4. Write the formal assumptions, user types, and query/workflow definitions for the report.
5. Decide whether to implement Kafka streaming or keep it as a documented pending requirement.
6. Design the umbrella frontend and define what each backend view needs to expose.
