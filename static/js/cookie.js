function getCookie(looking_for) {
    cookies = document.cookie.split(";");
    for (let index = 0; index < cookies.length; index++) {
        let each_cookie = cookies[index].split("=");
        if (each_cookie[0].trim().toLowerCase() == looking_for) {
            return (each_cookie[1].trim().toLowerCase())
        }
    }
    return false
}
