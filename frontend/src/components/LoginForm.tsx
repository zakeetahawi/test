import { useState } from 'react';
import axios from '../services/api';

export default function LoginForm() {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post('/auth/login/', credentials);
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        window.location.href = '/'; // Redirect to home page
      }
    } catch (err) {
      setError('اسم المستخدم أو كلمة المرور غير صحيحة');
    }
  };

  return (
    <div className="container">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card">
            <div className="card-header" style={{backgroundColor: 'var(--primary)', color: 'white'}}>
              <h5 className="mb-0"><i className="fas fa-sign-in-alt"></i> تسجيل الدخول</h5>
            </div>
            <div className="card-body">
              {error && (
                <div className="alert alert-danger">{error}</div>
              )}
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label">اسم المستخدم</label>
                  <input
                    type="text"
                    className="form-control"
                    value={credentials.username}
                    onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">كلمة المرور</label>
                  <input
                    type="password"
                    className="form-control"
                    value={credentials.password}
                    onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                  />
                </div>
                <div className="d-grid gap-2">
                  <button type="submit" className="btn" style={{backgroundColor: 'var(--primary)', color: 'white'}}>
                    <i className="fas fa-sign-in-alt"></i> تسجيل الدخول
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}