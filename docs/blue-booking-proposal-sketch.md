# Bluebooking Website Proposal Sketch
- This proposal sketch is an extension of the [[Bluebooking Proposal]]
- It will only cover the mandatory functionality laid out in the [[Bluebooking Proposal]]
	- Primarily the blogging use-cases will be discussed while the optionally chat use-cases will be ignored
- The project will use all-auth for authorisation which comes with some pre-built data structures
### Description
[Bluebooking](https://thealexandrian.net/wordpress/40005/roleplaying-games/ptolus-running-the-campaign-bluebooking) is a traditional TTRPG technique which allows for role-playing outside of the main game sessions. Historically, it involved sharing a notebook between players where they would write out in-character notes and scenes between their character and NPCs. Today, it is more commonly done via chat services.

This web application allows for online bluebooking within an TTRPG group. It functions similarly to a blogging service.

## Main user actions
###### Any user can:
- Create an user account
- Log-in to their account
- Edit their user account
- Delete their user account

- View a list of campaigns they are a member of
- View other members of a campaign they are a member of
- Accept invitation to a campaign
- Leave a campaign

###### Any player (including GM) can:
- View a list of all posts such as notes, announcements and sessions they can access
- Search or filter list of all posts they can access

- Write their own note
- Edit their own note
- Delete their own note
- Share notes with other players or GM

- Attach a post to a session

- View a list of the user's campaign personas
- Create a player persona
- Edit their player persona
- Delete their player persona

###### The GM can:
- Create a campaign (becoming the GM of the campaign)
- Edit their campaign
- Delete their campaign

- Invite a user to their own campaign
- Kick user from a campaign

- Promote another player to the GM role within the campaign
- Demote themself to the player role within the campaign

- Make an announcement
- Edit an announcement
- Delete an announcement
- Attach a post to an announcement

- Schedule a session
- Edit a session
- Delete a session

- Create a NPC persona
- Edit their NPC persona
- Delete their NPC persona

### Notes
- Posts are any type of user content
	- They can be announcements, sessions or notes
- The posts a user has access to is displayed in a user's feed
	- The posts in this feed are paginated
	- The feed is by default sorted from newest to oldest
- Posts in a Feed can by sorted by:
	- Time (newest-to-oldest or oldest-to-newest)
- Posts in a Feed can be filtered by:
	- A basic text search
	- A date range
	- Player, character or NPC involvement
	- Whether it is an as-player post or as-character post
	- Post type such as note, session and announcement
- Announcements are associated with a date, author, title and text contents in markdown
	- Author will always be GM however future extensions might allow GM to change
- Sessions are an extension of announcements, with the title automatically set to "Session [date]"
	- Posts that are not announcements themselves can be linked to an announcement by the GM
		- Anyone can link posts to a session announcement
- Notes are associated with a date, author, text contents in markdown
	- Notes are by default dated to the time of creation but they can be post or pre-dated.

## Data Model
The application should have the following data entities:
- Campaign, an entity representing a bluebooking group where users within the group can interact with each other. It is limited to 24 members.
- User, an entity representing the users of the application. It can have the role of GM or Player. It must be a member of ONE Party.
- Persona, an entity representing a persona of a User. It can be the player's main character or the NPC of the GM but it can also be the User's actual identity for out-of-character conversations. The persona's should have role representing whether it is a player, a character or a NPC.
- Post, an entity representing user generated content. It has a date, a title, an author (Persona) and text content as well as a list of users that can access it. It can be:
	- An announcement where by default the GM is the author and every User in the Party can access it.
	- An session where by default the GM is the author, every User in the campaign can access it and it's title includes "Session".
	- A note where by default it's only accessible by its author and the GM and the title field is empty.

## User Interface
- The user's feed should be the first page displayed past login.
- As-player or as-character or as-NPC posts should be displayed differently.
- Date-based filtering should be easy to use from the UI.
- Each character should be assigned a colour to use with their posts.
- Pagination should be clearly visible for posts.

## Main Architecture
```mermaid
flowchart LR
	subgraph Browser
		b1@{ shape: brace-r, label: "General Functions:<br>
		∙ Make HTML Page requests<br>
		∙ Render HTML Pages<br>
		∙ Style HTML using CSS and Tailwind<br>
		∙ Run JavaScript functions<br>
		∙ Load media such as images and videos<br>
		" }
		b2[["User's Browser<br><span style='font-size: 12px;'>User might use a Chromium browser such as Google Chrome or a popular alternative such as Safari or Firefox.</span>"]]
		b3@{ shape: comment, label: "HTMX Functions:<br>
		∙ Make partial page updates<br>
		∙ Send HX-Request headers<br>
		∙ Swap HTML fragments
		" }
	end
	Browser--Send HTTP requests-->w1
	
	subgraph Django Web Server
		w1["URL ROUTER<br><span style='font-size: 12px;'>
		∙ Receives all incoming HTTP request<br>
		∙ Rejects non-HTML/HTMX requests<br>
		∙ Routes HTML and HTMX request to the appropriate views<br>
		</span>
		"]
		w1--Routes HTML/HTMX to appropriate views-->w2
		
		w2["VIEWS<br><span style='font-size: 12px;'>
		∙ Handles HTML and HTMX requests<br>
		∙ Return full HTML pages or partial HTML fragments<br>
		∙ Generates HTML by inheriting HTML templates and persistent data<br>
		</span>
		"]
		w2--Use templates to structure HTML output-->w3
		w2--Use models to query persistent data-->w4
		
		w3["TEMPLATES<br><span style='font-size: 12px;'>
		∙ Represents the base immutable HTML which HTML responses inherit from<br>
		∙ Provides the foundation for how the HTML pages should be structured<br>
		</span>
		"]
		
		w4["MODELS<br><span style='font-size: 12px;'>
		∙ The Object-Relational Mapping between the Django Server and the Database<br>
		∙ Allows the database to be queried using Python code<br>
		</span>
		"]
	end
	w4--Send SQL Queries-->Database
	
	subgraph Database
		d1[("Postgres<br><span style='font-size: 10px;'>Final build database.</span>")]
		d2[("SQLite<br><span style='font-size: 10px;'>Temporary database used during developement.</span>")]
		d3@{ shape: comment, label: "Databases:<br>
		∙ Keep persistent data for all users<br>
		" }
	end
```
## Main User Flow
```mermaid
%%{init: {
  'flowchart': {
    'nodeSpacing': 20,
    'rankSpacing': 20,
  }
}}%%
flowchart LR
    %% List of Views/Pages in Web Application
	subgraph Authentication
		1[Log-in]
		2[Sign-up]
	end
	subgraph User
		3[User Home]
		4[User Settings]
		5[User Inbox]
	end
	subgraph Campaign
		6[Campaign Home]
		7[Campaign Create]
		8[Campaign Settings]
	end
	subgraph Personas
		9[Campaign Personas List]
		10[Persona Details]
		11[Presona Create]
		12[Persona Edit]
	end
	
	subgraph Posts
		subgraph Details
			13[Note Details]
			16[Annoucement Details]
			19[Session Details]
		end
		subgraph Create
			14[Note Create]
			17[Annoucement Create]
			20[Session Create]
		end
			15[Note Edit]
			18[Annoucement Edit]
			21[Session Edit]
	end
	
	%% Links between pages
	1==>|Successful Authentication|3
	2==>3
	3==>4
	3==>5
	3==>7
	3==>6
	6==>8
	6==>9
	9==>10
	9==>11
	9==>12
	10==>12
	
	6==>|Embedded into feed| Details
	6==>Create

	13==>15	
	16==>18
	19==>21
	
	%% Actions users can take on the pages
	classDef userAct fill:#d9e5f9,padding:0px,font-size:10px
	classDef playerAct fill:#efc2f9,padding:0px,font-size:10px
	classDef gmAct fill:#f99a9a,padding:0px,font-size:10px
	
	subgraph Authentication
		1---1a([Log-in to a user's account]):::userAct
		2---2b([Create an account]):::userAct
	end
	subgraph User
		3---3a([View list of campaigns a user is a member of]):::userAct
		3---3b([View other members of a campaign]):::userAct
		3---3c([Leave a campaign]):::userAct
		4---4a([Edit a user's account]):::userAct
		4---4b([Delete a user's account]):::userAct
		5---5a([Accept invitation to a campaign]):::userAct
	end
	subgraph Campaign
		6---6a([View a feed of all posts in the campaign that a user can access]):::playerAct
		6---6b([Search, filter or sort feed of posts that a user can access]):::playerAct
		7---7a([Create a campaign]):::userAct
		8---8a([View other members of a campaign]):::userAct
		8---8b([Leave a campaign]):::userAct
		8---8c([Edit a campaign]):::gmAct
		8---8d([Delete a campaign]):::gmAct
		8---8e([Invite a user to a own campaign]):::gmAct
		8---8f([Kick a user from a campaign]):::gmAct
		8---8g([Promote another player to the GM of campaign]):::gmAct
		8---8h([Demote themself to a player of the campaign]):::gmAct
	end
	subgraph Personas
		9---9a([View list of a user's campaign personas]):::playerAct
		11---11a([Create a player persona]):::playerAct
		11---11b([Create an NPC persona]):::gmAct
		12---12a([Edit a player persona]):::playerAct
		12---12b([Delete a player persona]):::playerAct
		12---12c([Edit an NPC persona]):::gmAct
		12---12d([Delete a NPC persona]):::gmAct
	end
	subgraph Posts
		14---14a([Write a note]):::playerAct
		15---15a([Edit a note]):::playerAct
		15---15b([Delete a note]):::playerAct
		15---15c([Share note with other players]):::playerAct
		16---16a([Attach a post to an annoucement]):::gmAct
		17---17a([Make an announcement]):::gmAct
		18---18a([Edit an announcement]):::gmAct
		18---18b([Delete an annoucement]):::gmAct
		19---19a([Attach a post to a session]):::playerAct
		20---20a([Schedule a session]):::playerAct
		21---21a([Edit a session]):::gmAct
		21---21b([Delete a session]):::gmAct
	end
```
## Main Data Entities
```mermaid
erDiagram
	%% Entities
	
	%% Entity representing the user details used for authentication and account management. It will be extended later to fulfil the all-auth user requirements.
	%% - email: unique, non-nullable
	USER {
		string id PK
		
		string email
		string passwordHash
		
		string name
		string displayName
		
		datetime createdAt
	}
	
	%% Entity representing a group of users where content can be shared between them freely. It is intended to broadly corresponds with a TTRPG campaign. A user can have the role PLAYER or GM within a campaign.
	CAMPAIGN {
		string id PK
		
		string title
		string description
		
		datetime createdAt
	}
	
	%% Entity representing a character that a user controls within a campaign. A user can have multiple personas, such as a user who is a player having a second player character due to the first one retiring or a GM controlling multiple NPCs. A persona is used to author and view content. By default a user will always have a persona that represents their real-world self to allow for meta-gaming content.
	%% - campaignId: non-nullable
	%% - userId: nullable
	PERSONA {
		string id PK
		string campaignId FK
		string userId FK
		
		string name
		string role
		
		datetime createdAt
		%% lastUsedAt recorded so that the most recently used persona can be listed in the UI
		datetime lastUsedAt
	}
	
	%% Entity representing an individual piece of content within a campaign feed. It can be an annoucement, session or note. It can be shared with other users.
	%% - campaign FK is non-nullable
	%% - persona FK is non-nullable
	POST {
		string id PK
		%% campaignId is redundant as persona includes campaign as a non-nullable FK however it makes querying the posts more efficient
		string campaignId FK 
		string personaId FK
		
		string title
		
		enum viewPermissionsState
		string content
		datetime createdAt
		datetime lastEditedAt
	}
	
	%% - campaign FK is non-nullable
	%% - sender FK is nullable
	%% - receiver FK is nullable
	INVITATION {
		string id PK
		string campaignId FK
		string senderId FK
		string receiverId FK
		
		datetime createdAt
		datetime expiredAt
	}
	
	%% Join Tables
	CAMPAIGN_MEMBERSHIP {
		string campaignId PK, FK
		string userId PK, FK
		
		enum role
		datetime createdAt
		datetime lastAccessedAt
	}
	
	POST_VIEW_PERMISSIONS {
		string postId PK, FK
		string personaId PK, FK
		
		datetime createdAt
	}
	
	POST_ATTACHMENTS {
		string hookPostId PK, FK
		string attachmentPostId PK, FK
		
		datetime createdAt
	}
	
	%% Relationships
	%% Core User-Campaign Relationship
	%% USER }o..o{ CAMPAIGN : "member of"
	USER ||..o{ CAMPAIGN_MEMBERSHIP : "has"
	CAMPAIGN ||..o{ CAMPAIGN_MEMBERSHIP : "has"
	
	%% Persona (controlled by user, contained by campaign)
	%% Persona is the identities that a user controls during the course of a campaign such as a player character or NPC
	%% If the user leaves the campaign or deletes their account, personas persist under the control of the GM
	%% A user can have multiple personas
	USER ||..|{ PERSONA : controls
	CAMPAIGN ||--o{ PERSONA : contains
	
	%% Post (authered by persona, contained by campaign)
	%% Posts are authored by a user within a campaign
	PERSONA ||--o{ POST : authors
	
	%% Post View Permissions
	%% Posts can be viewed by certain other users within a campaign
	%% PERSONA }o..o{ POST : "can view"
	PERSONA ||..o{ POST_VIEW_PERMISSIONS : "has"
	POST ||..o{ POST_VIEW_PERMISSIONS : "has"
	
	%% Invitation Flow
	%% The GM of a campaign can invite a user to join a campaign
	%% However as the GM of a campaign can change it must include a reference to the sender as well as the campaign it invites the receiver to
	USER ||..o{ INVITATION : receives
	USER ||..o{ INVITATION : authors
	CAMPAIGN ||--o{ INVITATION : generates
	
	%% Post Attachment
	%% A post can be attached to another post.
	POST ||..o{ POST_ATTACHMENTS : "is parent of"
	POST ||..o{ POST_ATTACHMENTS : "is child of"
```
