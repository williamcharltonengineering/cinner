
<p align="center">
  <img height=180 src="./readme_assets/logo.png">
</p>

It's a Python script that allows you to track the time spent working in your projects or tasks.
At the moment, this script doesn't have external dependencies so it's ready to run.

#### Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

#### Installation: 

`$ pip install cinner`

#### How to use:

**Help menu:**

`$ cinner -h`

```
usage: cinner [-h] [-p PATH] [-r] project

positional arguments:
  project               project name

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to the JSON data file
  -r, --report          Calculate and display a report of the time spent in the project
```

**Start/end working session**:

`$ cinner -p "~/Documents/my_project_time_tracker_data.json" "my_project"`

The file or project within the file will be created automatically if it doesn't exist.


#### Behavior

The script saves "timestamps" for the working sessions in a JSON file with the following structure:

```
{
   "projects": [
       {
           "project_name": "a_project_name",
           "sessions": [
              {
                  "start": "dd/mm/yy - H:M:S" ,
                  "end": "dd/mm/yy - H:M:S"
              }
           ]
       }
   ]
}
```
Unfinished sessions will have a `null` value in the `end` field.

#### Report

To calculate the time spent working in a project, run:

```
$ cinner -r -p "~/Documents/my_project_time_tracker_data.json" "my_project" 

Time spent working on project: 'my_project'
1 day, 7:52:19
Ongoing sessions: True
Time spent in ongoing session: 0:04:10.492647
```

#### TODO:

- [ ] add option to show hours (not days) in report
- [ ] add config option for billable rate ($/hr)
- [ ] add option to report on a calendar month
- [ ] add billable amount in report
- [ ] change date format to yyyy/m/d
