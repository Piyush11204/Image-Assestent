import  { useState } from 'react';
import { Loader2 } from 'lucide-react';

function QuestionAnswerApp() {
    const [image, setImage] = useState(null);
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleImageUpload = (e) => {
        const selectedImage = e.target.files[0];
        setImage(selectedImage);
        // Optional: Preview logic
        if (selectedImage) {
            const reader = new FileReader();
            reader.onloadend = () => {
                // You can add image preview logic here if needed
            };
            reader.readAsDataURL(selectedImage);
        }
    };

    const handleSubmit = async () => {
        // Reset previous state
        setLoading(true);
        setResponse(null);
        setError(null);

        // Validate image
        if (!image) {
            setError('Please upload an image first!');
            setLoading(false);
            return;
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('image', image);

        try {
            const res = await fetch('http://127.0.0.1:5000/answer-question', {
                method: 'POST',
                body: formData,
            });

            // Handle response
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || 'Failed to process the image');
            }

            const data = await res.json();
            setResponse(data);
        } catch (err) {
            console.error('Submission error:', err);
            setError(err.message || 'An unexpected error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto p-4 space-y-4">
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
                <div className="px-6 py-4 bg-gray-100 border-b">
                    <h2 className="text-xl font-semibold text-gray-800">Question Answering AI</h2>
                </div>
                <div className="p-6 space-y-4">
                    <input 
                        type="file" 
                        accept="image/*" 
                        onChange={handleImageUpload}
                        className="w-full p-2 border rounded-md text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:bg-violet-50 file:text-violet-700 hover:file:bg-violet-100"
                    />
                    
                    <button 
                        onClick={handleSubmit} 
                        disabled={loading}
                        className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            'Submit Question Image'
                        )}
                    </button>

                    {error && (
                        <div className="text-red-500 text-sm bg-red-50 p-2 rounded-md border border-red-200">
                            {error}
                        </div>
                    )}

                    {response && (
                        <div className="mt-4 space-y-4">
                            <div className="bg-white shadow-sm rounded-lg overflow-hidden">
                                <div className="px-4 py-3 bg-gray-100 border-b">
                                    <h3 className="text-md font-semibold text-gray-700">Extracted Question</h3>
                                </div>
                                <div className="p-4">
                                    <p className="text-sm text-gray-600">{response.extracted_question || 'No question found'}</p>
                                </div>
                            </div>

                            <div className="bg-white shadow-sm rounded-lg overflow-hidden">
                                <div className="px-4 py-3 bg-gray-100 border-b">
                                    <h3 className="text-md font-semibold text-gray-700">AI Answer</h3>
                                </div>
                                <div className="p-4">
                                    <p className="text-sm text-gray-600">{response.answer || 'No answer available'}</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default QuestionAnswerApp;