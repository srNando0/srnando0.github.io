/*

+---------------
| Basic Functions
+---------------

*/
function randomColor() {
	let r, g, b;
	
	r = Math.floor(256 * Math.random());
	g = Math.floor(256 * Math.random());
	b = Math.floor(256 * Math.random());
	
	return "rgb(" + r + "," + g + "," + b + ")";
}



/*

+---------------
| Events and Methods
+---------------

*/
/*
	Button onclick event for adding a circle
*/
function funButtonAddCircle(divCircles) {
	let circle;
	
	circle = document.createElement("div");
	
	circle.className = "circle";
	circle.style.backgroundColor = randomColor();
	circle.onclick = function() {
		circle.parentNode.removeChild(circle);
	}
	
	divCircles.appendChild(circle);
}



/*
	Event for creating elements in the DOM after the whole page is loaded
*/
function funBody() {
	let divPanel, divCircles, buttonAddCircle;
	
	
	
	divPanel		= document.createElement("div");
	divCircles		= document.createElement("div");
	buttonAddCircle	= document.createElement("button");
	
	
	
	divPanel.className			= "divPanel";
	divCircles.className		= "divCircles";
	buttonAddCircle.className	= "buttonAddCircle";
	
	buttonAddCircle.innerHTML	= "Add circle";
	
	buttonAddCircle.onclick	= function() { funButtonAddCircle(divCircles); };
	
	
	
	document.body.appendChild(divPanel);
	document.body.appendChild(divCircles);
	
	divPanel.appendChild(buttonAddCircle);
	
}



/*

+---------------
| Main
+---------------

*/
// linking the style file in head
let linkStyle;

linkStyle = document.createElement("link");

linkStyle.rel	= 'stylesheet';
linkStyle.type	= 'text/css';
linkStyle.href	= 'style.css';

document.head.appendChild(linkStyle);



// event for creating elements in the DOM after the whole page is loaded
window.onload = funBody;