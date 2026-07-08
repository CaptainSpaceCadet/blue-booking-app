# Commit Conventions
This repository follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. Git commits should be structured like this:
```gitcommit
<type>: <description>

[optional body]

[optional issue numbers]
```
An example commit structured like this would be:
```gitcommit
fix: remove typo from title screen

Remove typo from the title screen's main title.

#1
```
## The parts of the commit
### \<type\> [1](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13#types)
The type is a prefix that describes the overall category of the commit, it can be `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `docs`, `build` or `chore`.
#### Description of each type prefix
- Changes relevant to the API or UI:
    - `feat` Commits that add, adjust or remove a feature to/of/from the API or UI.
    - `fix` Commits that fix an API or UI bug of a preceded `feat` commit.
- `refactor` Commits that rewrite or restructure code without altering API or UI behaviour.
    - `perf` Commits are special type of `refactor` commits that specifically improve performance
- `style` Commits that address code style (e.g., white-space, formatting, missing semi-colons) and do not affect application behaviour.
- `test` Commits that add missing tests or correct existing ones.
- `docs` Commits that exclusively affect documentation.
- `build` Commits that affect build-related components such as build tools, dependencies, project version.
- `chore` Commits that represent tasks like initial commit or modifying `.gitignore`.
### \<description\> [2](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13#description)
The `description` contains a concise description of the change.
- The description is **mandatory**.
- It can be in English **or** Japanese.
- In English try, to use the imperative, present tense: "change" not "changed" nor "changes"
    - Think of `This commit will...` or `This commit should...`
- In English, **do not** capitalise the first letter
- **Do not** end the description with a period (`.` or `。`)
### \<body\> [3](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13#body)
The `body` should include the motivation for the change and contrast this with previous behaviour.
- The body is **optional**.
- It can in English **or** Japanese.
- In English, try to use the imperative present tense: "change" not "changed" nor "changes".
### \<issue numbers\>
In GitHub you can link a commit to an issue by referencing it's issue number.
- Linking to an issue is **optional**.
- Reference issue number via `#[number]` for example `#2`.
- Add an empty line between the end of the body and the list of issue numbers.
- Seperate the issue numbers with spaces for example `#1 #2 #3`.
## Examples of valid commits
```gitcommit
fix: remove typo from title screen

Remove typo from the title screen's main title.

#1
```

```gitcommit
fix: タイトルにタイポを書き直す

スクリーンのマインタイトルにタイポを書き直す。

#1
```

```gitcommit
feat: add notification on new direct messages
```

```gitcommit
feat: add save button to menu UI

#1 #4
```

```gitcommit
docs: add code conventions documentation

Describe code convention in markdown documents in both English and Japanese. Add a link to this documentation in the README.md.

#5 #6 #10
```

```gitcommit
refactor: change structure of movement checks
```

```gitcommit:
perf: decrease memory usage via use of singleton
```

```gitcommit
style: remove empty line
```
