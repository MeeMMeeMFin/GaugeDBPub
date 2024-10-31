console.log("Found script file!!");
const urlParams = new URLSearchParams(window.location.search);
const gameName = urlParams.get("game_name");
document.getElementById("gameName").textContent = gameName;


const testing = true;
function hostDefine(testing){
    if (testing){
        return "localhost"; //Non docker
    }else{
        return "admin-server"; //Docker
    };
};
var HOST_LOCATION = hostDefine(testing);


function unravelTopBy(word_data, top){
    let results = "";
    for (let i = 1; i <= top; i++) {
        console.log("Toimii looppi");
        let temp = word_data[i.toString()];
        console.log(word_data[i.toString()]);
        // temp[0] == word & temp[1] == correlation number
        results = results + `${temp[0]}: ${temp[1]}\r\n`;
    };
    console.log(results);
    return results;
};



async function getCorrelations(){
    let word1 = document.getElementById("word1").value;
    let word2 = document.getElementById("word2").value;
    let word3 = document.getElementById("word3").value;
    let word4 = document.getElementById("word4").value;
    let word5 = document.getElementById("word5").value;
    let block1 = document.getElementById("block1");
    let block2 = document.getElementById("block2");
    let block3 = document.getElementById("block3");
    let block4 = document.getElementById("block4");
    let block5 = document.getElementById("block5");
    let topEntriesAmount = Number(document.getElementById("topEntriesAmount").value);
    //let words = `${word1},${word2},${word3},${word4},${word5}`;
    let getUrl = `http://${HOST_LOCATION}:5008/api/v1/correlation_words_get?game_name=${gameName}&word1=${word1}&word2=${word2}&word3=${word3}&word4=${word4}&word5=${word5}`;
    let response = await fetch(getUrl);
    let data = await response.json();
    console.log(`data keys: ${Object.keys(data)}`);
    console.log("Toimii");
    block1.textContent = unravelTopBy(data[word1], topEntriesAmount);
    block2.textContent = unravelTopBy(data[word2], topEntriesAmount);
    block3.textContent = unravelTopBy(data[word3], topEntriesAmount);
    block4.textContent = unravelTopBy(data[word4], topEntriesAmount);
    block5.textContent = unravelTopBy(data[word5], topEntriesAmount);
};