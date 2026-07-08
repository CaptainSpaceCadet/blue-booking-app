# Branch Conventions
This repository follows an alteration the [Conventional Branch](https://conventionalbranch.org) specification. Git commits should be structured like this:
```gitbranch
<type>/(<issue>-)?<description>
```
An example branch structured like this would be:
```gitbranch
feature/1-add-login-page
```
## The parts of the commit
### \<issue\>
If the branch is related to a particular issue include the issue number in the name of the branch. If a branch is not related to any issue don't include any number.
- This is NOT in the standard [Conventional Branch](https://conventionalbranch.org) specification
### \<type\>[1](https://conventionalbranch.org/#branch-naming-prefixes)
The type is a prefix that describes the overall category of the branch, it can be `feature`, `bugfix`, `hotfix`, `release`.
#### Description of each type prefix
- **`feature/`** (or **`feat/`**): For new features (e.g., `feature/1-add-login-page`, `feat/1-add-login-page`)
- **`bugfix/`** (or **`fix/`**): For bug fixes (e.g., `bugfix/6-fix-header-bug`, `fix/10-header-bug`)
- **`hotfix/`**: For urgent fixes (e.g., `hotfix/9-security-patch`)
- **`release/`**: For branches preparing a release (e.g., `release/v1.2.0`)
- **`chore/`**: For non-code tasks like dependency, docs updates (e.g., `chore/update-dependencies`)
### \<description\>
The `description` contains a concise description of the branch's purpose. More specific rules on how the `description` is written is given [here](https://conventionalbranch.org/#basic-rules) specification.
