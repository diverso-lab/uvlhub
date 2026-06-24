function getMyCart() {
  const myCart = localStorage.getItem('myCart');
  if (myCart) {
    return JSON.parse(myCart);
  }
  return [];
}

function addToCart(id) {
  const myCart = getMyCart();
  if (myCart.includes(id)) {
    return;
  }
  myCart.push(id);
  localStorage.setItem('myCart', JSON.stringify(myCart));
  setCart();
}

function rmFromCart(id) {
  const myCart = getMyCart();
  const index = myCart.indexOf(id);
  if (index > -1) {
    myCart.splice(index, 1);
    localStorage.setItem('myCart', JSON.stringify(myCart));
  }
  setCart();
}

function clearCart() {
  localStorage.removeItem('myCart');
  setCart();
}

function countCart() {
  return getMyCart().length;
}

function setCart() {
  document.getElementById('amount-cart').innerText = countCart();
}

function goToMyCart() {
  let baseUrl = "/downloadqueue";
  let params = "?files=" + encodeURIComponent(getMyCart().toString());
  window.location.href = baseUrl + params;
}

setCart()


function removeElement(event, id) {
    event.parentElement.remove();
    rmFromCart(id);
}

function downloadAll() {
  let baseUrl = "/dataset/build/download/";
  let params = "?files=" + encodeURIComponent(getMyCart().toString());
  window.location.href = baseUrl + params;
}

function clearAll() {
  clearCart();
  document.getElementById("cart").innerHTML = "";
}

function buildDataset() {
  let baseUrl = "/dataset/upload";
  let params = "?with_hubfiles=" + encodeURIComponent(getMyCart().toString());
  window.location.href = baseUrl + params;
}