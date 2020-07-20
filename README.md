# Discord Friendly Fire Bot
## Bot Functions
1. Tracks number of friendly fire incidents using SQLite as the database

   Creates a database for each server the bot is in
   
2. Uses user mentions to track the aggressor and name to track the victim

   !tk @aggressor victim
   
   Also used for forgiveness 
   
   !forgive @aggressor victim
   
3. Has a leaderboard functionality

   !leaderboard

4. Each user's incidents can be seen with the number of times the aggressor has attacked a victim

   !total @aggressor
