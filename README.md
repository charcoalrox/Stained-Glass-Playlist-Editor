# Stained-Glass-Playlist-Editor

**Description:**
As someone who prefers to collect and own physical music files instead of streaming them, I run into issues using standard music players to edit my playlists. Windows Media Player is great but the inability to do things like make descriptions, look at multiple playlists at once, or delete more than one song without refreshing the page has made adding new music to my computer a really slow and tedious task. While I probably could have searched for software or tried VLC Media Player to do this instead, I thought it would be more fun to try and make my own and make sure I already had all of the features I wanted in a playlist editor by default. <br>
Aside from what's listed, Stained-Glass Playlist Editor is also capable of searching (with multiple search queries at the same time), playlist cleanup (remove duplicate songs from a playlist, convert all paths to local paths), music playing, and creating/destroying playlists on the fly. It's simple, it's ugly, but it's also perfectly effective at what it sets out to do.

<br><br>

**Setup:**
Setup is simple: Install the libraries in requirements.txt, swap out the phony paths in paths.json with the actual global paths to your music and playlists (playlists should be in a "playlists" folder inside of your music folder. I did this so that the playlists could be set up to easily work on my phone), and then run main.py

<br><br>

**Post-Mortem:**
I enjoyed this project. I don't have any regrets with the current functionality of the application and I do use it as my normal playlist editor so if I find any bugs, they're just going to be patched. Working with a system like PyQT5 for the first time was fun and it has a very nice workflow. I am aware that there's a GUI editor online that you can use instead of making everything manually and I would probably prefer to do that if I make anymore applications using it in the future but I wanted to make sure that I was learning how everything operated together so that I could comfortably use this library again in the future if I want to make any more GUI projects. Otherwise, this was a lot of nice practice with iterating over and modifying files inside of the operating system.<br>
If I continue working on this in the future, I would probably choose to make it a proper music player as well as a playlist editor. Really all it needs is the ability to queue multiple songs which isn't complicated to add by any means, I just didn't want to spend time doing that when the core functionality of the application was always going to be a focus on editing playlists. I also think it would have been really cool to click and drag songs straight from one List element into the playlists either in their own windows or from the list on the main page. Once again, this didn't sound like it would add anything to my program functionally. I don't think that it would be intuitive to users who aren't already familiar with the application and I don't think it would have been used much more than the context menus. <br>
