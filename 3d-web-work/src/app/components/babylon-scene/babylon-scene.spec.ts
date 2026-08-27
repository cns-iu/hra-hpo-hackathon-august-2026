import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BabylonScene } from './babylon-scene';

describe('BabylonScene', () => {
  let component: BabylonScene;
  let fixture: ComponentFixture<BabylonScene>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BabylonScene],
    }).compileComponents();

    fixture = TestBed.createComponent(BabylonScene);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
