import http from 'k6/http';

export const options = {
    vus:500,
    duration:"5s"
};
export default function () {
    http.get('http://127.0.0.1:8000/external');
}
