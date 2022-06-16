import os
import json
import unittest

from pathlib import Path
from src.xenocanto import Recording, get_recordings_list, download_recordings

class TestXenoCanto(unittest.TestCase):

  @classmethod
  def setUpClass(cls) -> None:
    cls.data_root = Path(f"{os.path.dirname(__file__)}/data/xenocanto")

  @classmethod
  def tearDownClass(cls) -> None:
    # remove test files
    [p.unlink() for p in list(cls.data_root.glob('*.mp3')) if p.is_file()]
    return super().tearDownClass()

  def test_create_recording_correct(self):
    """
    test creation of Recording objects
    """
    
    # create Recording object from a recording .json, as retrieved from xeno-canto API
    with open(self.data_root / "recordings_existent.json", 'r') as file:
      raw_recordings = json.load(file)
    
    recording = Recording.from_dict(raw_recordings['recordings'][0])

    self.assertEqual(recording.id, '541961')
    self.assertEqual(recording.genus, 'larus')
    self.assertEqual(recording.species, 'michahellis')
    self.assertEqual(recording.subspecies, 'lusitanius')
    self.assertEqual(recording.url, 'https://xeno-canto.org/541961/download')
    self.assertEqual(recording.audio_type, 'mp3')
    self.assertEqual(recording.filename, 'larus_michahellis_lusitanius_541961.mp3')

  def test_create_recording_incorrect(self):
    """
    test failure in creation of Recording objects
    """

    data = {
      'id' : '541961',
      'genus' : 'Larus',
      'subspecies' : 'lusitanius'
    }

    with self.assertRaises(KeyError):
      Recording.from_dict(data)

  def test_get_recordings_list_correct(self):
    """
    test get_recordings_list() against correct input
    """
    def _fake_adaptor(url:str) -> dict:
      with open(self.data_root / "recordings_existent.json", 'r') as file:
        return json.load(file)

    query = {'genus' : 'Larus', 'subspecies' : 'atlantis'}
    recordings = get_recordings_list(**query, api_adapter = _fake_adaptor)

    self.assertEqual(len(recordings), 2)
    self.assertTrue(all(isinstance(r, Recording) for r in recordings))
      
  def test_get_recordings_list_non_existent(self):
    """
    test get_recordings_list() with query for non-existent records
    """
    def _fake_adapter(url:str) -> dict:
      with open(self.data_root / "recordings_non_existent.json", 'r') as file:
        return json.load(file)

    query = {'genus' : 'Elusivus', 'subspecies' : 'gambuzinus'}
    recordings = get_recordings_list(**query, api_adapter = _fake_adapter)

    self.assertEqual(len(recordings), 0)

  def test_download_recordings_correct(self):
    """
    test download_recordings() against correct input
    """
    def _fake_adapter(url:str, path:Path):
      with open(path, 'w') as file:
        file.write('fake')
      return path

    with open(self.data_root / "recordings_existent.json", 'r') as file:
      raw_recordings = json.load(file)
    
    recordings = [Recording.from_dict(data) for data in raw_recordings['recordings']]
    
    # test download_recordings() with an empty output dir
    paths = download_recordings(recordings, self.data_root, download_adapter = _fake_adapter)
    self.assertEqual(len(paths), 2)
    self.assertTrue(all(r.id in paths for r in recordings))
    self.assertTrue(all(paths[r.id] == self.data_root / r.filename for r in recordings))

    # test download_recordings() with an non-empty output dir
    paths = download_recordings(recordings, self.data_root, download_adapter = _fake_adapter)
    self.assertEqual(len(paths), 0)

    # test download_recordings() with an non-empty output dir but force = True
    paths = download_recordings(recordings, self.data_root, force = True, 
      download_adapter = _fake_adapter)
    self.assertEqual(len(paths), 2)

    # test download_recordings() with a limit in downloads
    paths = download_recordings(recordings, self.data_root, limit = 1, force = True, 
      download_adapter = _fake_adapter)
    self.assertEqual(len(paths), 1)

  def test_download_recordings_wrong_wait(self):
    """
    test download_recordings() against incorrect wait time arguments
    """
    with self.assertRaises(ValueError):
      _ = download_recordings([], Path("data/xenocanto"), wait = 0)

if __name__ == '__main__':
  unittest.main()