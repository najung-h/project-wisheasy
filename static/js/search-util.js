let debounceTimer; // 디바운스 타이머 변수

/**
 * 디바운스 함수 (범용 유틸리티)
 * @param {Function} func - 실행할 함수
 * @param {number} delay - 지연 시간 (ms)
 */
function debounce(func, delay) {
    return function(...args) {
        clearTimeout(debounceTimer); // 이전 타이머 취소
        debounceTimer = setTimeout(() => {
            func.apply(this, args); // 정해진 시간 후 함수 실행
        }, delay);
    };
}

/**
 * 역 검색 API 호출 함수 (범용 유틸리티)
 * @param {string} query - 사용자가 입력한 검색어
 * @returns {Promise<Array>} - 검색 결과 (예: [{name: "강남역", line: "2호선"}])
 */
async function fetchStations(query) {
    // 검색어가 비어있으면 빈 배열 반환
    if (!query || query.trim() === "") {
        return [];
    }

    // 이 URL은 Django stations/urls.py에 정의할 경로입니다.
    const url = `/api/stations/search/?q=${encodeURIComponent(query)}`;

    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            // HTTP 에러 처리
            console.error("API request failed:", response.status);
            return [];
        }

        const data = await response.json();
        // Django view에서 {'results': [...]} 형태로 반환한다고 가정
        return data.results; 

    } catch (error) {
        // 네트워크 에러 등 fetch 자체의 에러 처리
        console.error("Error fetching stations:", error);
        return [];
    }
}