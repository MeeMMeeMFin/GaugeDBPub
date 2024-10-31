console.log("Found script file!!");

const testing = true;
function hostDefine(testing){
    if (testing){
        return "localhost"; //Non docker
    }else{
        return "admin-server"; //Docker
    };
};
const HOST_LOCATION = hostDefine(testing);



//function databaseExpress(){
//    location.href = "http://localhost:8081/";
//};

// TODO Check existance
async function checkExistance(){
    let game_name = document.getElementById("gameId").value;
    let button = document.getElementById("checkExistanceButton");
    let result = `http://${HOST_LOCATION}:5008/check_existance?game_name=${game_name}`;
    //let statusNumber;
    let response = await fetch(result,{credentials: "include"});
    if(response.status!=200){
        button.style.background="#ed1212";
        button.textContent = "False";
        //alert("\nWith error:\n"+ response);
        setTimeout(() => {alert("\nWith error:\n"+ response);}, 800);
    }else{
        button.style.background="#1be45f";
        button.textContent = "True";
    };
};
// TODO Process game
async function processGame(){
    let game_name = document.getElementById("gameId").value;
    console.log(`preprocessing ${game_name}...`);
    let button = document.getElementById("processGameButton");
    button.style.background= "rgb(170, 170, 170)";
    button.textContent = "Working...";
    let response;
    // TODO change url
    let result = `http://${HOST_LOCATION}:5008/api/v1/process_game?game_name=${game_name}`;
    await fetch(result)
    .then((response)=>response = response);
    if(response.status!=200){
        button.style.background="#ed1212";
        button.textContent = "False";
        setTimeout(() => {alert(response.text() +"\nWith error:\n"+ response.status);}, 800);
    }else{
        button.style.background="#1be45f";
        button.textContent = "done processing";
    };
    button.textContent = "Process game";
};

// TODO Build number graph
function buildNumberGraph(){
    let game_name = document.getElementById("gameId").value;
    let button = document.getElementById("buildNumberGraphButton");
    let result = `http://${HOST_LOCATION}:5008/api/v1/build/raw_number_graph?game_name=${game_name}`;
    //alert(result);
    let response;
    fetch(result)
    .then((response)=>response = response);
    if(response.status!=200){
        button.style.background="#ed1212";
        button.textContent = "False";
        setTimeout(() => {alert(response.text() +"\nWith error:\n"+ response.status);}, 800);
    };
};

// TODO Build correlation
async function buildCorrelation(){
    let game_name = document.getElementById("gameId").value;
    let button = document.getElementById("buildCorrelationButton");
    // TODO change url
    let result = `http://${HOST_LOCATION}:5008/api/v1/build/number_correlation?game_name=${game_name}`;
    let response ="";
    response = await fetch(result);
    alert(response.text);
    //.then((response)=>response);
    //if(response.status!=200){
    //    button.style.background="#ed1212";
    //    alert(response.text() +"\nWith error:\n"+ response.status)
    //};
};

// TODO Check correlation
function checkCorrelation(){
    let game_name = document.getElementById("gameId").value;
    // TODO change url
    let newUrl = `http://${HOST_LOCATION}:5008/api/v1/correlation_page?game_name=${game_name}`;
    document.location.href = newUrl;
};

// TODO Forecast today
async function forecastToday(){
    let game_name = document.getElementById("gameId").value;
    let forecastBox = document.getElementById("forecastBox");
    // TODO change url
    let result = `http://${HOST_LOCATION}:5008/api/v1/forecast/today_votes_up?game_name=${game_name}`;
    let response = await fetch(result);
    let data = await response.json();
    forecastBox.textContent = `${game_name}'s todays votes_up:\r\n${data["number"]}`;
};

// TODO RE-CREATE AI
function reCreateAi(){
    let game_name = document.getElementById("gameId").value;
    let button = document.getElementById("reCreateAiButton");
    // TODO change url
    let result = `http://${HOST_LOCATION}:5008/api/v1/build_new_ai/raw_number_graph`;
    let response;
    fetch(result)
    .then((response)=>response = response);
    if(response.status!=200){
        button.style.background="#ed1212";
        button.textContent = "False";
        setTimeout(() => {alert(response.text() +"\nWith error:\n"+ response.status);}, 800);
    } else{
        button.textContent = "Done";
        setTimeout(() => {alert("Ai created");}, 800); 
    };
};




//gameIdForm = document.getElementById("gameIdForm");

//gameIdForm.addEventListener("submit", processData);
