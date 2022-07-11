# pydepl
 pydepl is a (very) simple utility to automate tasks
### ..but there are countless tools that do these things, couldnt'you use one of  those?
Yes of course, this tool was never meant to copy ( or compete ) with other projects, it was born as a wrapper over a specific script on a single server and then it "evolved" when that script was getting too big.
## Usage
You must provide a file defining the pipeline of tasks to be executed and then point that file to pydepl
```sh

python pydepl -p <pipeline.[json|yml]>
```
### Pipeline
The pipeline is where you define the task(s) to be executed and the context ( variables ) to set up your environment.
```yml
    version: 1
        context:
            my-host: localhost
            my-remote: remote_srv_name
            my-var: world
            destdir: $HOME
        task_list:
            - task:
                task_name: task2
                host: "{my-host}"
                type: shell
                cmd: "echo hello {my-var}"
```
This defines a pipeline with 1 task, as you can see the syntax is very simple, you can define global ( relative to the pipeline ) variables and use them in every Task. You can use environment variables ( relative to the host running pydepl) simply by providing a $ and the variable name.
### Task
A task is the unit doing the work, you define a task by populating these properties:
>
    task_name: name of the Task

    host: The host where the command will be executed

    cmd: the actual cmd to execute ( you can use variables from the pipeline or specific to this task)

    type: defines the type of the running task, at the moment there are 3 types: shell, shellout and scp

### task types
Tasks can be of different types, at the moment only 3 are supported:
> shell -> the cmd will be executed on the shell
> 
> shellout -> it works as the shell type but saves the output in a variable into the context
> 
> scp -> copy the file defined by cmd from host to dest


With shellout tasks you can dynamically modify the context of the running pipeline, for example you can define varialbles from the output of programs running on different servers and then use them  ( that's the main reason this tool was born...):
```yml
    version: 1
        context:
            my-host: localhost
            my-remote: remote_srv_name
            my-remote2: remote2_srv_name
            my-var: world
            destdir: $HOME
        task_list:
            - task:
                task_name: task1
                host: "{my-remote}"
                type: shellout
                out_var: srv-1-var
                cmd: "uname -sr"
            - task:
                task_name: task2
                host: "{my-remote2}"
                type: shellout
                out_var: srv-2-var
                cmd: "uname -sr"
            - task:
                task_name: task3
                host: "{my-host}"
                type: shell
                cmd: "echo my-var: {my-var}, srv1: {srv-1-var}, srv2: {srv-2-var}"
            
```
## Improvement
 These features were planned:
 - [] Refactor TaskType
 - [] Group Task in TaskGroup
 - [] Add support for concurrent Task/TaskGropup
 - [] Add events/hooks support ( on Task started, etc... )
 - [] Add support for different OS types
  
  ## Author
  frmx