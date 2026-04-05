document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const name = document.getElementById('bookName').value;
  const dailyGoal = document.getElementById('dailyGoal').value;
  const file = document.getElementById('bookFile').files[0];
  
  if (!name || !file) {
    alert('Заполните все поля');
    return;
  }
  
  const formData = new FormData();
  formData.append('name', name);
  formData.append('daily_goal', dailyGoal);
  formData.append('file', file);
  
  const token = getToken();
  
  try {
    const response = await fetch(`${API_URL}/books/books/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`
      },
      body: formData
    });
    
    if (response.ok) {
      alert('Книга успешно добавлена!');
      window.location.href = '/';
    } else {
      const error = await response.json();
      alert(error.error || 'Ошибка загрузки книги');
    }
  } catch (error) {
    alert('Ошибка загрузки книги');
  }
});