# Contributing to swampymud

Thank you for helping out with the Open Source Club's SwampyMud project!

Following these guidelines helps us keep good project workflow. We appreciate your help.

Our community guidelines are described in [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
Hop in our [discord](https://discord.gg/SCqmG3x) for any additional questions or just to hangout!

## How do I help?

Please check the **[Issues](https://github.com/ufosc/MuddySwamp/issues)** pages for current tasks.
If you see something that you would like to help with, ask about helping in a comment.
If you're just starting out, checkout our **[beginner friendly](https://github.com/ufosc/MuddySwamp/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)** issues for ways to help. 

Check out the [DESIGN.md](./DESIGN.md) file for a high level explanation of the project.

## Reporting Bugs

Check to see if someone already reported this [bug](https://github.com/ufosc/MuddySwamp/issues).
If so then comment on that issue.
If not, provide a detailed description of the bug.
Include what happened before the error, all settings, and test results. This helps us more quickly identify and solve any problems.
**[Create an Issue](https://github.com/ufosc/MuddySwamp/issues/new)** with the description and add the `bug` label.

## Requesting a Feature

Check our [design document](DESIGN.md) and other [issues](https://github.com/ufosc/MuddySwamp/issues) to see if the feature has already been requested. If so, then feel free to add your thoughts on that issue. If not, **[create an Issue](https://github.com/ufosc/MuddySwamp/issues/new)** with the description and add the `feature` label. 

## Testing on your own server

Any contributors working on scripts or engine code should test their code before submitting it. 

To test server code on your own machine, run

```
python3 -m swampymud
```

Then with a telnet client, you will connect to the following IP like so:

```
telnet 127.0.0.1 1234
```

Alternatively, you can use Mudlet or another MUD client. 
Follow the instructions provided in [README.md](README.md) and use "127.0.0.1" and "1234" as the address and port, respectively. 

Test thoroughly, and maybe we can avoid some headaches down the line.

## Unit Testing
This package has several testcases found in `./tests/` created with python's `unittest` module. You can run the testcases like so:
```
python3 -m unittest
```
Running the unittest module will automatically find the testcases in `./tests/` and execute them.

## Submitting Changes 

1. Create a fork or branch to tackle a specific issue 
	- Team members branch off of dev and follow this [guide](https://guides.github.com/introduction/flow/) 
	- Others make a [fork](https://guides.github.com/activities/forking/)
  	- Name it after the issue or feature you are working on
2. Follow the style guidelines below 
	- This helps with debugging and working on the project
3. Make small incremental commits
	- It's easier to find issues when only a small amount of code is changed
4. Thoroughly test your changes (see the section above).
    - (Always run `python3 -m unittest` before submitting.)
5. Make a pull request 
	- The request will be reviewed
	- Any needed changes will be noted 
6. The changes will be added to the project 
	- Yay! Thanks for the help. 

## Style Guide 

Use our **[.editorconfig]()** to help automatically format your code.

Python is meant to be a **readable**. We follow [PEP8](https://www.python.org/dev/peps/pep-0008/) and you should too.

You can also find our complete introduction to Python [here](https://github.com/ufosc/club-resources/tree/master/python).
