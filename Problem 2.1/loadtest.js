import http from "k6/http";

export const options = {
    vus: 10,
    duration: "5s",
};

export default function () {
    http.get("http://127.0.0.1:8000/course-progress/42");
}