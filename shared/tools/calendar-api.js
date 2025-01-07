export async function getNextAppointment() {
    try {
        const response = await fetch('http://localhost:8000/calendar/next');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error accessing calendar:', error);
        throw new Error(`Failed to get calendar events: ${error.message}`);
    }
} 