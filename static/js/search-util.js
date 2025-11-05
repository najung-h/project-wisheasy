
const CHO = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];
const JUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'];
const JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];

/**
 * Decomposes a Hangul string into its constituent Jamo characters (초성, 중성, 종성).
 * @param {string} hangul The string to decompose.
 * @returns {string} The decomposed string.
 */
function decomposeHangul(hangul) {
    let result = '';
    for (let i = 0; i < hangul.length; i++) {
        const charCode = hangul.charCodeAt(i);
        
        // Not a Hangul syllable
        if (charCode < 0xAC00 || charCode > 0xD7A3) {
            result += hangul[i];
            continue;
        }

        const syllableIndex = charCode - 0xAC00;
        const choIndex = Math.floor(syllableIndex / (21 * 28));
        const jungIndex = Math.floor((syllableIndex % (21 * 28)) / 28);
        const jongIndex = syllableIndex % 28;

        result += CHO[choIndex] + JUNG[jungIndex];
        if (jongIndex > 0) {
            result += JONG[jongIndex];
        }
    }
    return result;
}

/**
 * Checks if a target string starts with a query string, supporting Hangul Jamo and prefix matching.
 * Ignores spaces and hyphens.
 * @param {string} target The string to search within (e.g., a station name).
 * @param {string} query The search query from the user.
 * @returns {boolean} True if the target starts with the query.
 */
function hangulStartsWith(target, query) {
    // Normalize by removing spaces/hyphens and decomposing Hangul characters
    const normalizedTarget = decomposeHangul(target.replace(/[\s-]/g, ''));
    const normalizedQuery = decomposeHangul(query.replace(/[\s-]/g, ''));

    if (normalizedQuery.length === 0) {
        return false; // Do not show suggestions for empty query
    }
    
    return normalizedTarget.startsWith(normalizedQuery);
}

function getLineClass(line) {
    const lineMap = {
        '1호선': '1',
        '2호선': '2',
        '3호선': '3',
        '4호선': '4',
        '5호선': '5',
        '6호선': '6',
        '7호선': '7',
        '8호선': '8',
        '9호선': '9',
        '분당선': 'bundang',
        '경의중앙선': 'gyeongui',
    };
    return lineMap[line] || '2';
}

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