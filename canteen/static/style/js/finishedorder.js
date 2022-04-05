function yesorno(){
    document.getElementById('finish').innerHTML = '';
    document.getElementById('yes').innerHTML = '<button type="button" class="btn btn-success" display="inline-block" onclick="notFinish()">Yes</button>';
    document.getElementById('no').innerHTML = '<button type="button" class="btn btn-danger" display="inline-block" onclick="notFinish()">No</button>';
}
  
function notFinish(){
    document.getElementById('finish').innerHTML = '<button type="button" class="btn btn-primary" onclick="yesorno()">Finish</button>';
    document.getElementById('yes').innerHTML = ''
    document.getElementById('no').innerHTML = ''
}