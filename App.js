import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Components
const Header = ({ currentView, setCurrentView }) => (
  <header className="bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg">
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">ArtistHub</h1>
        <nav className="flex space-x-6">
          <button
            onClick={() => setCurrentView('discover')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              currentView === 'discover' ? 'bg-white text-purple-600' : 'hover:bg-purple-500'
            }`}
          >
            Discover
          </button>
          <button
            onClick={() => setCurrentView('upload')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              currentView === 'upload' ? 'bg-white text-purple-600' : 'hover:bg-purple-500'
            }`}
          >
            Upload
          </button>
          <button
            onClick={() => setCurrentView('profile')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              currentView === 'profile' ? 'bg-white text-purple-600' : 'hover:bg-purple-500'
            }`}
          >
            Profile
          </button>
        </nav>
      </div>
    </div>
  </header>
);

const ArtistCard = ({ artist, onClick }) => (
  <div 
    className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow cursor-pointer overflow-hidden"
    onClick={() => onClick(artist)}
  >
    <div className="h-48 bg-gradient-to-r from-blue-400 to-purple-500 flex items-center justify-center">
      {artist.profile_image ? (
        <img 
          src={`data:image/jpeg;base64,${artist.profile_image}`}
          alt={artist.name}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="text-white text-6xl font-bold">
          {artist.name.charAt(0).toUpperCase()}
        </div>
      )}
    </div>
    <div className="p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-2">{artist.name}</h3>
      <p className="text-gray-600 mb-2">{artist.location}</p>
      <p className="text-gray-700 text-sm line-clamp-3">{artist.bio}</p>
    </div>
  </div>
);

const ContentCard = ({ content, artist }) => {
  const isImage = content.file_type.startsWith('image/');
  const isVideo = content.file_type.startsWith('video/');
  const isAudio = content.file_type.startsWith('audio/');

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      <div className="h-64 bg-gray-100 flex items-center justify-center">
        {isImage ? (
          <img 
            src={`data:${content.file_type};base64,${content.file_data}`}
            alt={content.title}
            className="w-full h-full object-cover"
          />
        ) : isVideo ? (
          <video 
            src={`data:${content.file_type};base64,${content.file_data}`}
            controls
            className="w-full h-full object-cover"
          />
        ) : isAudio ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="text-4xl text-gray-400">🎵</div>
            <audio 
              src={`data:${content.file_type};base64,${content.file_data}`}
              controls
              className="w-full"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <div className="text-4xl text-gray-400">📄</div>
            <p className="text-gray-600">{content.file_name}</p>
          </div>
        )}
      </div>
      <div className="p-4">
        <h4 className="text-lg font-bold text-gray-800 mb-2">{content.title}</h4>
        <p className="text-gray-600 text-sm mb-2">by {artist?.name}</p>
        <p className="text-gray-700 text-sm mb-3">{content.description}</p>
        {content.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {content.tags.map((tag, index) => (
              <span key={index} className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const DiscoverView = ({ artists, content, onArtistClick }) => (
  <div className="container mx-auto px-4 py-8">
    <div className="mb-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Discover Artists</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {artists.map((artist) => (
          <ArtistCard key={artist.id} artist={artist} onClick={onArtistClick} />
        ))}
      </div>
    </div>

    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Latest Works</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {content.map((item) => {
          const artist = artists.find(a => a.id === item.artist_id);
          return <ContentCard key={item.id} content={item} artist={artist} />;
        })}
      </div>
    </div>
  </div>
);

const UploadView = ({ artists, onRefresh }) => {
  const [selectedArtist, setSelectedArtist] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedArtist || !title || !file) {
      alert('Please fill in all required fields');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('artist_id', selectedArtist);
      formData.append('title', title);
      formData.append('description', description);
      formData.append('tags', tags);
      formData.append('file', file);

      await axios.post(`${API}/content`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      alert('Content uploaded successfully!');
      setTitle('');
      setDescription('');
      setTags('');
      setFile(null);
      onRefresh();
    } catch (error) {
      console.error('Upload error:', error);
      alert('Error uploading content');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-3xl font-bold text-gray-800 mb-8">Upload Your Work</h2>
        
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-md p-8 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Artist *
            </label>
            <select
              value={selectedArtist}
              onChange={(e) => setSelectedArtist(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            >
              <option value="">Choose an artist...</option>
              {artists.map((artist) => (
                <option key={artist.id} value={artist.id}>
                  {artist.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="abstract, digital, painting"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              File *
            </label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              accept="image/*,audio/*,video/*,.pdf,.doc,.docx"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload Content'}
          </button>
        </form>
      </div>
    </div>
  );
};

const ProfileView = ({ artists, onRefresh }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newArtist, setNewArtist] = useState({
    name: '',
    email: '',
    bio: '',
    location: '',
    website: '',
  });

  const handleCreateArtist = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/artists`, newArtist);
      alert('Artist profile created successfully!');
      setNewArtist({
        name: '',
        email: '',
        bio: '',
        location: '',
        website: '',
      });
      setShowCreateForm(false);
      onRefresh();
    } catch (error) {
      console.error('Create artist error:', error);
      alert('Error creating artist profile');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Artist Profiles</h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-2 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-colors"
          >
            {showCreateForm ? 'Cancel' : 'Create New Profile'}
          </button>
        </div>

        {showCreateForm && (
          <div className="bg-white rounded-xl shadow-md p-8 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-6">Create Artist Profile</h3>
            <form onSubmit={handleCreateArtist} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Name *</label>
                  <input
                    type="text"
                    value={newArtist.name}
                    onChange={(e) => setNewArtist({...newArtist, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
                  <input
                    type="email"
                    value={newArtist.email}
                    onChange={(e) => setNewArtist({...newArtist, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                  <input
                    type="text"
                    value={newArtist.location}
                    onChange={(e) => setNewArtist({...newArtist, location: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Website</label>
                  <input
                    type="url"
                    value={newArtist.website}
                    onChange={(e) => setNewArtist({...newArtist, website: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bio</label>
                <textarea
                  value={newArtist.bio}
                  onChange={(e) => setNewArtist({...newArtist, bio: e.target.value})}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-colors"
              >
                Create Profile
              </button>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {artists.map((artist) => (
            <ArtistCard key={artist.id} artist={artist} onClick={() => {}} />
          ))}
        </div>
      </div>
    </div>
  );
};

function App() {
  const [currentView, setCurrentView] = useState('discover');
  const [artists, setArtists] = useState([]);
  const [content, setContent] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [artistsResponse, contentResponse] = await Promise.all([
        axios.get(`${API}/artists`),
        axios.get(`${API}/content`)
      ]);
      
      setArtists(artistsResponse.data);
      setContent(contentResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleArtistClick = (artist) => {
    console.log('Artist clicked:', artist);
    // TODO: Implement artist detail view
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading amazing artists...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentView={currentView} setCurrentView={setCurrentView} />
      
      {currentView === 'discover' && (
        <DiscoverView 
          artists={artists} 
          content={content} 
          onArtistClick={handleArtistClick} 
        />
      )}
      
      {currentView === 'upload' && (
        <UploadView 
          artists={artists} 
          onRefresh={fetchData} 
        />
      )}
      
      {currentView === 'profile' && (
        <ProfileView 
          artists={artists} 
          onRefresh={fetchData} 
        />
      )}
    </div>
  );
}

export default App;
