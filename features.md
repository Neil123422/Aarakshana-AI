## Feaures to add: 
1. a restart button on the prompt just in case prompt fails to go through the API 
2. a prompt edit button to redo the prompt without typing out the whole thing (done, buggy)
3. a paralegal compatible prompt transform button to give the maximum results on prompting  (done, does not work)
4. A pop-up menu appearing on right click similar to claude in which it shows rename chat, delete chat, move to: followed by a small search bar pop up and on searching it shows the available chats with the same name (should not be case sensitive, to be an ease of access feature)  





## Bugs to fix: 
1. to show the whole prompt expanding vertically if the prompt is very long. Dynamic expansion of prompting region as per the length of the prompt. (not fixed)
2. File upload and reading. it does not show any preview of the upload in the prompting region. And also integrate it in a way such that the prompt sends the file and then it does not show anymore in the prompting window. It shows a preview in the final prompt sent ahead. Then it gets processed by the model (it reads the content inside) and on the basis of that it gives an output.  
3. Allocation of cloud storage of the sessions, allocation of memory dedicated to the files uploaded (upto 100mb per session)
4. The edit button just sends a new prompt to the prompting window. I want it seamless like I want that exported prompt bubble ui to be edited like gemini/claude
    EXISTING BUG: it shows an edit option, but the color of the font in the edit box is odd, plus there's a HTML static ring showing inside it which looks ugly.It also does not send the prompt upon editing its soft locked inside that edit box. 
5. The restart button starts a new result, i want to edit the old response. I also want the prompt edit feature to edit the existing response only, not generate a new one.
