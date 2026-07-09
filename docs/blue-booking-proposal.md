# Bluebooking Website Proposal
## Description
Bluebooking is a traditional TTRPG technique which allows for role-playing outside of the main game sessions. It involved sharing a notebook between players where they would write out in-character notes and scenes between their character and NPCs. Nowadays it is commonly done via chat services.

The proposed web application allows for easy bluebooking within an TTRPG group. It functions primarily as a blogging service.
## Main user actions
**The player can:**
- Write their own note
- Edit or delete their own note
- Share notes with other players or GM
- Attach a post to a session
- View a list of all posts such as notes, announcements, sessions ([optional] and chats) they can access
- Search or filter list of all posts they can access
- [optional] Create a chat as a player between other players or GM
- [optional] Create a chat between other characters or NPCs (GM) as a character
- [optional] Send and receive messages on a chat
- [optional] Choose to deactivate a chat
- [optional] Display a list of active chats
**The GM can:**
- Write their own note
- Edit or delete their own note
- Share notes with player
- ==GM Only== Only Make an announcement
- ==GM Only== Schedule a session
- ==GM Only== Attach a post to an announcement
- Attach a post to a session
- View a list of all posts such as notes, announcements, sessions ([optional] and chats) they can access
- Search or filter list of all posts they can access
- [optional] Create a chat as the GM with players
- [optional] Create a chat as an NPCs between other characters or NPCs
- [optional] Send and receive messages on a chat
- [optional] Choose to deactivate a chat
- [optional] Display a list of active chats
### Notes
- Posts are any type of user content
	- They can be announcements, sessions, notes ([optional] or chats)
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
	- Post type such as note, session, announcement ([optional] or chat)
- Announcements are associated with a date, author, title and text contents in markdown
	- Author will always be GM however future extensions might allow GM to change
- Sessions are an extension of announcements, with the title automatically set to "Session [date]"
	- Posts that are not announcements themselves can be linked to an announcement by the GM
		- Anyone can link posts to a session announcement
- Notes are associated with a date, author, text contents in markdown
	- Notes are by default dated to the time of creation but they can be post or pre-dated.
- [optional] Chats are associated with a start date, an author, a title, and a series of messages
	- [optional] Chats are either active or inactive
	- [optional] The messages should be paginated within a chat
- [optional] Messages are associated with a timestamp, a sender, and text content in markdown
- [optional] The markdown in posts can contain uploaded images

## Data Model
The application should have the following data entities:
- Party, an entity representing a bluebooking group where users within the group can interact with each other. It is limited to 24 members.
- User, an entity representing the users of the application. It can have the role of GM or Player. It must be a member of ONE Party.
- Persona, an entity representing a persona of a User. It can be the player's main character or the NPC of the GM but it can also be the User's actual identity for out-of-character conversations. The persona's should have role representing whether it is a player, a character or a NPC.
- Post, an entity representing user generated content. It has a date, a title, an author (Persona) and text content as well as a list of users that can access it. It can be:
	- An announcement where by default the GM is the author and every User in the Party can access it.
	- An session where by default the GM is the author, every User in the Party can access it and it's title includes "Session".
	- A note where by default it's only accessible by its author and the GM and the title field is empty.
	- [optional] A chat where by default it has no text content. It also links to an active chat or inactive chat entity.
- [optional] Active Chat, an entity representing a conversation between Personas (be it in-character or out-of-character). It has a list of messages.
- [optional] Inactive Chat, an entity representing a conversation between Personas (be it in-character or out-of-character) that has been deactivated so no more messages can be sent. It contains text which is just a list of all of the messages' content.
- [optional] Message, an entity representing a message from a persona as part of a chat.

## User Interface
- The user's feed should be the first page displayed past login.
- As-player or as-character or as-NPC posts should be displayed differently.
- Date-based filtering should be easy to use from the UI.
- Each character should be assigned a colour to use with their posts.
- Pagination should be clearly visible for posts ([optional] and chats).
- [optional] Active chats should be able to be accessed from a seperate tab seperate from the feed.
