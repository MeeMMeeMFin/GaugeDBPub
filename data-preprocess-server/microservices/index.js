console.log("Found script file!!")

function databaseExpress(){
    location.href = "http://localhost:8081/";
};

function processData(){
    let game_name = document.getElementById("gameId").value;
    result = "http://localhost:5001/api/v1/process_game?game_name=" + game_name
    alert(result)
    location.href = "http://localhost:5001/api/v1/process_game?game_name=" + game_name;
};

gameIdForm = document.getElementById("gameIdForm")

gameIdForm.addEventListener("submit", processData)
