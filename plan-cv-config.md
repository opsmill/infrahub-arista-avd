
# Analyse

Read @docs/plan-cv-config-check.md for the task context.
Read the docs of this project (@docs/docs)

Explore the ways in which we could sync the InfraHub proposed changes lifecycle with the CloudVision Workspace. The way I see it is:

- When opening a proposed change in InfraHub, a CloudVision workspace is automatically created to validate the configuration -> This is what is implemented today
- When deleting the proposed change in InfraHub, the corresponding workspace should be abandoned
- When merging a proposed change in InfraHub, the user should have a choice to submit or not the workspace. Keep in mind that, even highly improbable, a workspace submission can fail. We should avoid ending in a state where the proposed changes has merged but the CloudVision workspace could not be submitted.

I see the Semaphore component that could then execute the deployment (which is the change control execution in CloudVision), eventually, we could use Semaphore to submit the workspace and handle the error, if any.

# Plan

-