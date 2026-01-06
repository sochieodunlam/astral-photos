let availableKeywords = ["Hello", "Goodbye", "Hello friends"]

const inputBox = document.getElementById("input-box")

inputBox.onkeyup = function() {
    let result = []
    let input = inputBox.value

    if (input.length) {
        result = availableKeywords.filter(function(keyword) {
            return keyword.toLowerCase().includes(input.toLowerCase()) //TODO: add "no results found div if result.length == 0"
        })
        var resultBox = document.getElementById("result-box")
        var allDivs = document.createElement("div")
        resultBox.append(allDivs)

        for (let x = 0; x < 6; x++) {
            var newDiv = document.createElement("div")
            allDivs.append(newDiv)
            newDiv.textContent = result[x]
        }
        document.addEventListener("click", function() {
                allDivs.remove();
            })
        document.addEventListener("keydown", function() {
                allDivs.remove();
            })
        
    }
    
}