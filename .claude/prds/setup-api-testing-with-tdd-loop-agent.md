This is the high level overview from the user. The agent should expand this strategically through a conversation with
@socratic-coder.md & @naming-expert


- Setup a best practice API testing pipeline to enable us to do TDD on the API
- - Search for a pragmatic set of python testing solutions to quickly start and increase the test coverage of the API code
- - Propose 2+ testing setups and recommend the best one that matches our current project
- - Add next steps for an analyst to analyze the integration points
- - Add next steps for a prompt-generator to create a claude command that knows only the key points for how to run all tests, or subtests.
- - Create a super concise high-level-overview.md that shows the files created to agentically run the testing loop on the API
- - - high-level-overview.md should be a short tree command like output that explains what files need to be run to test the known parts of our pipeline
- - - the correct configuration files are created to hook the AI back into this new command, or documentation.

ENSURE WHATEVER TESTING FRAMEWORK WE USE CAN BE INCLUDED IN AGEMTS.MD OR CLAUDE.MD TO TEACH THE AI HOW TO USE THE TESTS
ENSURE CLEAR AI DOCUMENTATION IS CREATED FOR THE KEY "GETTING STARTED" COMMANDS


```high-level-overview.md hypothetical example.

# I. Testing the ingestion pipeline

## Tree-like output of the key tests and description of the module / system / file it tests.
├── fake-folder
│   └── fake-something
│       ├── some-test-file
│       ├── some-source-file

## How to run the test
### `Command examples such as 'pytest ingestion-tests/*'`


## Special cases / special tests specific to the API

lorem ipsum

# II. Testing the X

# III. Testing for valid embeddings
```