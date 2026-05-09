let transacoes = JSON.parse(
localStorage.getItem("transacoes") || "[]"
);

function abrirModal(){

document.getElementById("modal")
.style.display = "flex";

}

function fecharModal(){

document.getElementById("modal")
.style.display = "none";

}

function salvarTransacao(){

const nome = document.getElementById("nome").value;
const valor = Number(
document.getElementById("valor").value
);
const tipo = document.getElementById("tipo").value;
const mes = document.getElementById("mes").value;

if(!nome || !valor){
alert("Preencha tudo");
return;
}

transacoes.push({
nome,
valor,
tipo,
mes
});

localStorage.setItem(
"transacoes",
JSON.stringify(transacoes)
);

fecharModal();
render();

}

function excluir(index){

transacoes.splice(index,1);

localStorage.setItem(
"transacoes",
JSON.stringify(transacoes)
);

render();

}

function render(){

const lista = document.getElementById("lista");

lista.innerHTML = "";

let entradas = 0;
let gastos = 0;

transacoes.forEach((t,index)=>{

if(t.tipo === "entrada"){
entradas += t.valor;
}else{
gastos += t.valor;
}

lista.innerHTML += `
<div class="item">

<div class="info">
<h3>${t.nome}</h3>
<p>${t.tipo} • ${t.mes}</p>
</div>

<div>
<div class="valor">
R$ ${t.valor}
</div>

<button class="excluir"
onclick="excluir(${index})">
Excluir
</button>
</div>

</div>
`;

});

const saldo = entradas - gastos;


document.getElementById("saldoTotal")
.innerText = `R$ ${saldo}`;


document.getElementById("totalEntradas")
.innerText = `R$ ${entradas}`;


document.getElementById("totalGastos")
.innerText = `R$ ${gastos}`;

}

function filtrarMes(){

const filtro = document.getElementById("filtroMes").value;

if(filtro === "todos"){
render();
return;
}

const lista = document.getElementById("lista");

lista.innerHTML = "";

transacoes
.filter(t => t.mes === filtro)
.forEach((t,index)=>{

lista.innerHTML += `
<div class="item">

<div class="info">
<h3>${t.nome}</h3>
<p>${t.tipo} • ${t.mes}</p>
</div>

<div>
<div class="valor">
R$ ${t.valor}
</div>

<button class="excluir"
onclick="excluir(${index})">
Excluir
</button>
</div>

</div>
`;

});

}

function gerarPDF(){
alert("PDF premium em desenvolvimento");
}

function logout(){

localStorage.removeItem("token");
localStorage.removeItem("username");

window.location.href = "/";

}

render();
